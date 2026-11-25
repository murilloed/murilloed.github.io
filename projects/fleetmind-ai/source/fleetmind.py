"""Seeded fleet simulator, demand regression, parameter-shared Q repositioning."""
import argparse
import csv
import json
import math
import random
from pathlib import Path

CITIES={'compact':{'rate':.55,'hot':4},'commuter':{'rate':.8,'hot':0},'distributed':{'rate':1.,'hot':8}}
def distance(a,b):return abs(a%3-b%3)+abs(a//3-b//3)
def neighbors(zone):return [z for z in range(9) if distance(zone,z)<=1]
def step_toward(a,b):return min(neighbors(a),key=lambda z:(distance(z,b),z))
def poisson(rng,rate):
    threshold=math.exp(-rate);product=1.;k=0
    while product>threshold:k+=1;product*=rng.random()
    return k-1
def requests(city='compact',seed=7,horizon=120):
    cfg=CITIES[city];rng=random.Random(seed);data=[]
    for t in range(horizon):
        for z in range(9):
            rate=cfg['rate']*(.3+(.9 if z==cfg['hot'] else 0))*(1+.4*math.sin(2*math.pi*t/60))
            for _ in range(poisson(rng,rate)):
                destination=rng.choice([d for d in range(9) if d!=z])
                data.append({'id':len(data),'minute':t,'origin':z,'destination':destination})
    return data
def state(zone,minute):return (zone,(minute//15)%4)

def simulate(data,fleet_size=16,policy='nearest',q=None,seed=7,horizon=120,train=False):
    if policy not in ('random','nearest','qlearning'):raise ValueError('unknown policy')
    if fleet_size<1:raise ValueError('fleet must be positive')
    rng=random.Random(seed);q=q if q is not None else {}
    vehicles=[{'id':i,'zone':i%9,'task':None,'phase':'idle','previous':None} for i in range(fleet_size)]
    pending=[];completed=[];assigned=[];expired=[];trace=[];empty_steps=0;occupied_steps=0;waits=[]
    by_minute={}
    for r in data:
        if not (0<=r['origin']<9 and 0<=r['destination']<9 and r['minute']>=0):raise ValueError('invalid request')
        by_minute.setdefault(r['minute'],[]).append(dict(r))
    for minute in range(horizon):
        pending.extend(by_minute.get(minute,[]))
        for r in pending[:]:
            if minute-r['minute']>12:pending.remove(r);expired.append(r)
        # FCFS request order, nearest idle vehicle or random-vehicle baseline.
        for r in pending[:]:
            available=[v for v in vehicles if v['task'] is None]
            if not available:break
            v=rng.choice(available) if policy=='random' else min(available,key=lambda v:(distance(v['zone'],r['origin']),v['id']))
            v['task']=r;v['phase']='pickup';pending.remove(r);assigned.append(r['id'])
        for v in vehicles:
            reward=0.;r=v['task']
            if r is not None:
                if v['phase']=='pickup' and v['zone']==r['origin']:
                    waits.append(minute-r['minute']);v['phase']='occupied';reward+=1
                target=r['destination'] if v['phase']=='occupied' else r['origin']
                if v['zone']!=target:
                    v['zone']=step_toward(v['zone'],target)
                    if v['phase']=='occupied':occupied_steps+=1
                    else:empty_steps+=1;reward-=.05
                if v['phase']=='occupied' and v['zone']==r['destination']:
                    completed.append({**r,'completed_minute':minute});v['task']=None;v['phase']='idle';reward+=2
            current=state(v['zone'],minute)
            if train and v['previous'] is not None:
                old,action=v['previous'];key=(old,action)
                future=max(q.get((current,a),0.) for a in neighbors(v['zone'])) if minute<horizon-1 else 0
                q[key]=q.get(key,0.)+.12*(reward+.9*future-q.get(key,0.))
            action=v['zone']
            if r is None and policy=='qlearning':
                options=neighbors(v['zone'])
                action=rng.choice(options) if train and rng.random()<.2 else max(options,key=lambda a:(q.get((current,a),0.),a==v['zone'],-a))
                if action!=v['zone']:empty_steps+=1
                v['zone']=action
            v['previous']=(current,action)
        active=sum(v['task'] is not None for v in vehicles)
        trace.append({'minute':minute,'vehicles':[{'id':v['id'],'zone':v['zone'],'phase':v['phase']} for v in vehicles],'pending':len(pending),'completed':len(completed),'active':active})
    active=sum(v['task'] is not None for v in vehicles)
    arrived=sum(r['minute']<horizon for r in data)
    metrics={'requests':arrived,'completed':len(completed),'active':active,'pending':len(pending),'expired':len(expired),'completion_rate':len(completed)/arrived if arrived else 0,'mean_pickup_wait_min':sum(waits)/len(waits) if waits else None,'empty_km':empty_steps*.5,'occupied_km':occupied_steps*.5}
    assert metrics['requests']==metrics['completed']+active+len(pending)+len(expired)
    return {'metrics':metrics,'trace':trace}

def train_q(city='compact',episodes=24):
    q={}
    for episode in range(episodes):simulate(requests(city,100+episode),policy='qlearning',q=q,seed=episode,train=True)
    return q

def features(t,z):return [1.,math.sin(2*math.pi*t/60),math.cos(2*math.pi*t/60)]+[float(z==i) for i in range(9)]
def forecast(city):
    def dataset(seeds):
        rows=[]
        for seed in seeds:
            counts={}
            for r in requests(city,seed):counts[(r['minute'],r['origin'])]=counts.get((r['minute'],r['origin']),0)+1
            rows.extend((features(t,z),counts.get((t,z),0)) for t in range(120) for z in range(9))
        return rows
    training=dataset(range(30,36));test=dataset(range(70,73));weights=[0.]*12
    # Full-batch gradient descent with L2 penalty, no test data in fitting.
    for _ in range(180):
        gradient=[0.]*12
        for x,y in training:
            error=sum(a*b for a,b in zip(x,weights))-y
            for i in range(12):gradient[i]+=error*x[i]/len(training)
        weights=[w-.18*(g+.01*w) for w,g in zip(weights,gradient)]
    baseline=sum(y for _,y in training)/len(training)
    rmse=lambda errors:math.sqrt(sum(errors)/len(errors))
    return {'model':'L2 linear regression, seasonal + zone features','train_seeds':list(range(30,36)),'test_seeds':list(range(70,73)),'heldout_rmse':rmse([(max(0,sum(a*b for a,b in zip(x,weights)))-y)**2 for x,y in test]),'mean_baseline_rmse':rmse([(baseline-y)**2 for _,y in test]),'weights':weights,'unit':'requests / zone / minute','synthetic':True}

def validate_csv(path):
    with Path(path).open(encoding='utf-8-sig') as handle:
        rows=list(csv.DictReader(handle))
    required={'minute','observed','simulated'}
    if not rows or not required.issubset(rows[0]):raise ValueError('CSV requires minute,observed,simulated')
    minutes=[int(r['minute']) for r in rows]
    pairs=[(float(r['observed']),float(r['simulated'])) for r in rows]
    if len(set(minutes))!=len(minutes) or any(m<0 for m in minutes):raise ValueError('minutes must be unique and nonnegative')
    if any(not math.isfinite(v) or v<0 for pair in pairs for v in pair):raise ValueError('counts must be finite and nonnegative')
    return {'rows':len(rows),'mae':sum(abs(a-b) for a,b in pairs)/len(rows),'rmse':math.sqrt(sum((a-b)**2 for a,b in pairs)/len(rows)),'note':'Paired counts supplied by user; units, provenance, time alignment and real-world status require external verification.'}

def load_requests(path):
    with Path(path).open(encoding='utf-8-sig') as handle:
        rows=list(csv.DictReader(handle))
    if not rows or not {'minute','origin','destination'}.issubset(rows[0]):raise ValueError('request CSV requires minute,origin,destination')
    result=[]
    for i,row in enumerate(rows):
        t,a,b=(int(row[k]) for k in ('minute','origin','destination'))
        if t<0 or not 0<=a<9 or not 0<=b<9 or a==b:raise ValueError('invalid minute or zone')
        result.append({'id':i,'minute':t,'origin':a,'destination':b})
    return sorted(result,key=lambda r:(r['minute'],r['id']))

def export_requests(data,path):
    with Path(path).open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=['id','minute','origin','destination'])
        writer.writeheader();writer.writerows(data)

def experiment():
    cases=[];forecasting={}
    for city in CITIES:
        q=train_q(city);forecasting[city]=forecast(city)
        for fleet in (8,16,24):
            for policy in ('random','nearest','qlearning'):
                runs=[simulate(requests(city,seed),fleet,policy,q,seed) for seed in (7,8,9)]
                cases.append({'city':city,'fleet':fleet,'policy':policy,'seeds':[7,8,9],'metrics':{k:sum(r['metrics'][k] or 0 for r in runs)/len(runs) for k in runs[0]['metrics']},'individual_metrics':[r['metrics'] for r in runs],'trace_seed':7,'trace':runs[0]['trace']})
    return {'synthetic':True,'horizon_min':120,'zone_edge_km':.5,'minutes_per_edge':1,'training':{'episodes':24,'seeds':[100,123],'fleet':16,'epsilon':.2,'alpha':.12,'gamma':.9,'state':'zone and time bin; shared table across vehicles','actions':'stay or adjacent zone; only idle vehicles reposition','reward':'pickup +1, completed +2, pickup travel -0.05; simplified credit assignment'},'scenarios':cases,'forecast':forecasting,'limitations':['No observed operational dataset was used.','Three stylized grids, not calibrated named cities.','Parameter-shared tabular Q-learning is exploratory, not deep multi-agent RL.','Reward approximates service; learned policy may underperform nearest baseline.','No road congestion, charging, battery or autonomous control model.','Reported scenario metrics average three seeds; traces show seed 7 only.','Forecast is evaluated on held-out synthetic seeds, not a real-city benchmark.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='report.json');p.add_argument('--observed')
    p.add_argument('--single',action='store_true');p.add_argument('--city',choices=CITIES,default='compact')
    p.add_argument('--fleet',type=int,default=16);p.add_argument('--policy',choices=['random','nearest','qlearning'],default='nearest')
    p.add_argument('--seed',type=int,default=7);p.add_argument('--requests');p.add_argument('--export-demand');args=p.parse_args()
    if args.observed:result=validate_csv(args.observed)
    elif args.single or args.requests or args.export_demand:
        data=load_requests(args.requests) if args.requests else requests(args.city,args.seed)
        if args.export_demand:export_requests(data,args.export_demand)
        q=train_q(args.city) if args.policy=='qlearning' else {}
        result={'synthetic':None if args.requests else True,'data_source':'user CSV, provenance unverified' if args.requests else 'seeded synthetic Poisson requests','city':args.city,'seed':args.seed,'fleet':args.fleet,'policy':args.policy,'horizon_min':120,'q_training_source':'synthetic seeds 100..123' if q else None,**simulate(data,args.fleet,args.policy,q,args.seed)}
    else:result=experiment()
    Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
