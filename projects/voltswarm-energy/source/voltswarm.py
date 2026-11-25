"""Multi-vehicle EV dispatch, queue-aware charging and a contextual bandit."""
import argparse
import csv
import json
import math
import random
from pathlib import Path

STATIONS={0:1,7:2,15:1}
CITIES={'balanced':{'demand':1.4,'energy':.20,'outage':False},'commuter':{'demand':2.,'energy':.20,'outage':False},'storm':{'demand':1.8,'energy':.27,'outage':True}}
def distance(a,b):return abs(a%4-b%4)+abs(a//4-b//4)
def step(a,b):
    if a%4!=b%4:return a+(1 if b%4>a%4 else -1)
    return a+(4 if b//4>a//4 else -4) if a!=b else a
def poisson(rng,rate):
    k=0;p=1.;threshold=math.exp(-rate)
    while p>threshold:k+=1;p*=rng.random()
    return k-1
def demand(city,seed,horizon=180):
    rng=random.Random(seed);rows=[]
    for t in range(horizon):
        for _ in range(poisson(rng,CITIES[city]['demand']*(1+.35*math.sin(t/25)))):
            a=rng.choice([0,1,4,5]) if city=='commuter' and rng.random()<.6 else rng.randrange(16)
            b=rng.choice([z for z in range(16) if z!=a]);rows.append({'id':len(rows),'minute':t,'origin':a,'destination':b})
    return rows
def key(zone,station,load):return f'{zone//4}:{station}:{min(2,load//3)}'
def simulate(city='balanced',fleet=16,policy='reservation',seed=7,model=None,train=False,horizon=180):
    if city not in CITIES or policy not in ('nearest','reservation','bandit') or fleet<1:raise ValueError('invalid scenario')
    cfg=CITIES[city];cost=cfg['energy'];rng=random.Random(seed+900);model=model if model is not None else {}
    vehicles=[{'id':i,'zone':i%16,'battery':3.2+(i%5)*.55,'phase':'idle','task':None,'station':None,'choice':None} for i in range(fleet)]
    initial=sum(v['battery'] for v in vehicles);charged=consumed=0.;wait=0;completed=0;expired=0;pending=[];pickup=[];trace=[];minimum=12.;peak_kw=0.;requests=demand(city,seed,horizon)
    arrivals={}
    for r in requests:arrivals.setdefault(r['minute'],[]).append(r)
    def ports(s,t):return 0 if cfg['outage'] and s==7 and 65<=t<105 else STATIONS[s]
    for t in range(horizon):
        pending.extend(dict(r) for r in arrivals.get(t,[]))
        overdue=[r for r in pending if t-r['minute']>15];expired+=len(overdue);pending=[r for r in pending if t-r['minute']<=15]
        # Reserve charging destinations before matching trips. No vehicle moves twice per minute.
        for v in vehicles:
            if v['phase']!='idle' or v['battery']>=3.5:continue
            candidates=[s for s in STATIONS if distance(v['zone'],s)*cost<=v['battery'] and ports(s,t)>0]
            if not candidates:v['phase']='stranded';continue
            loads={s:sum(w['station']==s for w in vehicles) for s in candidates}
            def estimate(s):
                travel=distance(v['zone'],s)
                fallback=travel+max(0,loads[s]-STATIONS[s]+1)*12/STATIONS[s]+12
                if policy=='nearest':return travel
                if policy=='reservation':return fallback
                learned=model.get(key(v['zone'],s,loads[s]))
                return learned['mean'] if learned else fallback
            station=rng.choice(candidates) if train and rng.random()<.2 else min(candidates,key=lambda s:(estimate(s),s))
            v['choice']=(key(v['zone'],station,loads[station]),t);v['station']=station;v['phase']='to_charge'
        for r in pending[:]:
            options=[]
            for v in vehicles:
                if v['phase']!='idle':continue
                energy=(distance(v['zone'],r['origin'])+distance(r['origin'],r['destination'])+min(distance(r['destination'],s) for s in STATIONS))*cost+.3
                if energy<=v['battery']:options.append(v)
            if not options:continue
            v=min(options,key=lambda w:(distance(w['zone'],r['origin']),w['id']));v['task']=r;v['phase']='pickup';pending.remove(r)
        for v in vehicles:
            phase=v['phase'];r=v['task']
            if phase=='pickup' and v['zone']==r['origin']:
                pickup.append(t-r['minute']);v['phase']='occupied';phase='occupied'
            if phase in ('pickup','occupied','to_charge'):
                target=v['station'] if phase=='to_charge' else r['origin'] if phase=='pickup' else r['destination']
                if v['zone']!=target:
                    if v['battery']+1e-9<cost:v['phase']='stranded';continue
                    v['zone']=step(v['zone'],target);v['battery']-=cost;consumed+=cost
                if v['zone']==target:
                    if phase=='to_charge':v['phase']='queued'
                    elif phase=='occupied':completed+=1;v['task']=None;v['phase']='idle'
        power=0
        for s in STATIONS:
            queue=sorted((v for v in vehicles if v['station']==s and v['phase'] in ('queued','charging')),key=lambda v:(v['choice'][1],v['id']))
            for i,v in enumerate(queue):
                if i>=ports(s,t):v['phase']='queued';wait+=1;continue
                v['phase']='charging';energy=min(.5,9.-v['battery']);v['battery']+=energy;charged+=energy;power+=energy*60
                if v['battery']>=9.-1e-9:
                    if train:
                        k,begin=v['choice'];entry=model.setdefault(k,{'n':0,'mean':0.});entry['n']+=1;entry['mean']+=(t-begin+1-entry['mean'])/entry['n']
                    v['phase']='idle';v['station']=None;v['choice']=None
        minimum=min(minimum,min(v['battery'] for v in vehicles));peak_kw=max(peak_kw,power)
        assert all(-1e-8<=v['battery']<=12 for v in vehicles)
        active=sum(v['task'] is not None for v in vehicles)
        assert sum(r['minute']<=t for r in requests)==completed+expired+len(pending)+active
        trace.append({'minute':t,'vehicles':[{'id':v['id'],'zone':v['zone'],'phase':v['phase'],'soc':round(v['battery']/12,3)} for v in vehicles],'stations':[{'zone':s,'ports':ports(s,t),'queue':sum(v['station']==s and v['phase']=='queued' for v in vehicles)} for s in STATIONS],'completed':completed,'pending':len(pending),'power_kw':power})
    final=sum(v['battery'] for v in vehicles);balance=initial+charged-consumed-final
    assert abs(balance)<1e-7
    return {'metrics':{'requests':len(requests),'completed':completed,'completion_rate':completed/len(requests) if requests else 0,'expired':expired,'pending':len(pending),'active':sum(v['task'] is not None for v in vehicles),'charge_queue_vehicle_min':wait,'mean_pickup_wait_min':sum(pickup)/len(pickup) if pickup else 0,'traction_kwh':consumed,'charged_kwh':charged,'energy_balance_error_kwh':balance,'minimum_battery_kwh':minimum,'peak_grid_kw':peak_kw,'stranded':sum(v['phase']=='stranded' for v in vehicles)},'trace':trace}
def train_model(city):
    model={}
    for seed in range(100,112):simulate(city,16,'bandit',seed,model,train=True)
    return model
def experiment():
    scenarios=[];models={}
    for city in CITIES:
        model=train_model(city);models[city]=model
        for fleet in (12,24):
            for policy in ('nearest','reservation','bandit'):
                runs=[simulate(city,fleet,policy,s,model) for s in (7,8,9)]
                scenarios.append({'city':city,'fleet':fleet,'policy':policy,'seeds':[7,8,9],'individual_metrics':[r['metrics'] for r in runs],'metrics':{k:sum(r['metrics'][k] for r in runs)/3 for k in runs[0]['metrics']},'trace_seed':7,'trace':runs[0]['trace']})
    return {'synthetic':True,'scenarios':scenarios,'learned_models':models,'protocol':{'training_seeds':list(range(100,112)),'test_seeds':[7,8,9],'learning':'Contextual sample-mean bandit estimates time to finish charging; epsilon .2 during training only. Censored unfinished charging decisions do not update estimates.','battery_kwh':12,'target_charge_kwh':9,'charge_kw_per_port':30,'edge_km':.8,'minutes_per_edge':1,'traction_kwh_per_edge':{c:x['energy'] for c,x in CITIES.items()},'horizon_min':180,'outage':'storm: station 7 offline from minute 65 through 104','dispatch':'Nearest feasible idle vehicle; trip requires energy for pickup, passenger route and return to a charger plus 0.3 kWh reserve.'},'limitations':['Stylized micro-EV fleet, not a physical vehicle model. No real charging sessions or grid data used.','Bandit is not deep RL; no performance or convergence guarantee.','Reservations approximate queue load; not a grid optimizer or enforceable booking system.','Models train at fleet size 16; evaluation at 12/24 tests limited transfer.','Zero modeled stranding under tested inputs is not an operational safety guarantee.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='report.json');p.add_argument('--single',action='store_true');p.add_argument('--city',choices=CITIES,default='balanced');p.add_argument('--fleet',type=int,default=16);p.add_argument('--policy',choices=['nearest','reservation','bandit'],default='reservation');p.add_argument('--seed',type=int,default=7);p.add_argument('--export-demand');args=p.parse_args()
    if args.export_demand:
        with Path(args.export_demand).open('w',newline='',encoding='utf-8') as handle:
            writer=csv.DictWriter(handle,fieldnames=['id','minute','origin','destination']);writer.writeheader();writer.writerows(demand(args.city,args.seed))
    result={'synthetic':True,**simulate(args.city,args.fleet,args.policy,args.seed,train_model(args.city) if args.policy=='bandit' else None)} if args.single else experiment()
    Path(args.output).write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
