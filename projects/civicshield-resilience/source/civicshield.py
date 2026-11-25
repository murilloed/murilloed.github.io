"""Adversarial scenario search and district-aware multi-vehicle mobility planning."""
import argparse
import csv
from collections import deque
import json
import math
import random
from pathlib import Path

CITIES=('grid','river','ladder')
def edges(city):
    if city not in CITIES:raise ValueError('unknown topology')
    result=[]
    for z in range(16):
        x,y=z%4,z//4
        if x<3 and not (city=='river' and x==1 and y not in (0,3)):result.append((z,z+1))
        if y<3 and not (city=='ladder' and x not in (0,3)):result.append((z,z+4))
    return result
def path(city,start,goal,closed=None):
    adjacency={z:[] for z in range(16)}
    for a,b in edges(city):
        if closed is not None and set((a,b))==set(closed):continue
        adjacency[a].append(b);adjacency[b].append(a)
    previous={start:None};queue=deque([start])
    while queue:
        a=queue.popleft()
        if a==goal:
            route=[]
            while a is not None:route.append(a);a=previous[a]
            return route[::-1]
        for b in adjacency[a]:
            if b not in previous:previous[b]=a;queue.append(b)
    return []
def demand(city,seed,event,horizon=100):
    rng=random.Random(seed);rows=[]
    for t in range(horizon):
        # Same seeded exogenous requests for every evaluated policy.
        for z in range(16):
            rate=.08*(1+.4*math.sin(t/15))
            if z in (0,1,4,5):rate*=1.6
            if 30<=t<60 and z==event['hotspot']:rate*=event.get('surge',5)
            k=0;product=1.;threshold=math.exp(-rate)
            while product>threshold:k+=1;product*=rng.random()
            for _ in range(k-1):rows.append({'id':len(rows),'minute':t,'origin':z,'destination':rng.choice([d for d in range(16) if d!=z])})
    return rows
def learn_rates(city):
    counts=[1.]*16;exposure=10*100
    for seed in range(100,110):
        for r in demand(city,seed,{'hotspot':seed%16,'surge':3}):counts[r['origin']]+=1
    return [c/(exposure+1) for c in counts]
def simulate(city='river',fleet=12,policy='robust',seed=7,event=None,rates=None,horizon=100):
    if policy not in ('nearest','equity','robust') or fleet<1:raise ValueError('invalid policy or fleet')
    event=event or {'hotspot':15,'edge':0,'surge':5};rates=rates or [1/16]*16
    links=edges(city);event={**event,'edge':int(event['edge'])%len(links)}
    vehicles=[{'id':i,'zone':i%16,'phase':'idle','task':None} for i in range(fleet)]
    rows=demand(city,seed,event,horizon);arrivals={};arrived_zone=[0]*16;served_zone=[0]*16;pending=[];completed=expired=0;wait=[];trace=[];blocked_min=0;repositions=0
    for r in rows:arrivals.setdefault(r['minute'],[]).append(r)
    for t in range(horizon):
        closed=links[event['edge']] if 30<=t<65 else None
        for r in arrivals.get(t,[]):pending.append(dict(r));arrived_zone[r['origin']]+=1
        old=[r for r in pending if t-r['minute']>12];expired+=len(old);pending=[r for r in pending if t-r['minute']<=12]
        idle=[v for v in vehicles if v['task'] is None]
        # Global iterative auction: all feasible request–vehicle bids compete.
        while pending and idle:
            bids=[]
            for v in idle:
                for r in pending:
                    pickup=path(city,v['zone'],r['origin'],closed);trip=path(city,r['origin'],r['destination'],closed)
                    if not pickup or not trip:continue
                    deficit=1-served_zone[r['origin']]/max(1,arrived_zone[r['origin']])
                    score=t-r['minute']-(len(pickup)-1)
                    if policy!='nearest':score+=7*deficit
                    if policy=='robust':
                        # Penalize assignments whose route would fail under the chosen event.
                        disrupted=path(city,r['origin'],r['destination'],links[event['edge']])
                        risk=8 if not disrupted else max(0,len(disrupted)-len(trip))
                        score-=.6*risk+.15*(len(trip)-1)
                    bids.append((score,-r['id'],-v['id'],v,r))
            if not bids:break
            *_,v,r=max(bids,key=lambda bid:bid[:3]);v['task']=r;v['phase']='pickup';pending.remove(r);idle.remove(v)
        for v in vehicles:
            r=v['task']
            if r is not None:
                if v['phase']=='pickup' and v['zone']==r['origin']:v['phase']='occupied';wait.append(t-r['minute'])
                target=r['origin'] if v['phase']=='pickup' else r['destination'];route=path(city,v['zone'],target,closed)
                if not route:blocked_min+=1;continue
                if len(route)>1:v['zone']=route[1]
                if v['phase']=='occupied' and v['zone']==r['destination']:completed+=1;served_zone[r['origin']]+=1;v['task']=None;v['phase']='idle'
            elif policy=='robust':
                loads=[sum(w['zone']==z and w['task'] is None for w in vehicles) for z in range(16)]
                targets=[]
                for z in range(16):
                    route=path(city,v['zone'],z,closed)
                    if route:
                        deficit=1-served_zone[z]/max(1,arrived_zone[z]);value=rates[z]*(1+deficit)/(1+loads[z])-.015*(len(route)-1)
                        targets.append((value,-z,route))
                if targets:
                    route=max(targets,key=lambda x:x[:2])[2]
                    if len(route)>1:v['zone']=route[1];repositions+=1
        active=sum(v['task'] is not None for v in vehicles)
        assert sum(arrived_zone)==completed+active+expired+len(pending)
        trace.append({'minute':t,'vehicles':[{'id':v['id'],'zone':v['zone'],'phase':v['phase']} for v in vehicles],'closed':closed,'hotspot':event['hotspot'] if 30<=t<60 else None,'arrived_zone':arrived_zone[:],'served_zone':served_zone[:],'completed':completed,'pending':len(pending)})
    ratios=[served_zone[z]/arrived_zone[z] for z in range(16) if arrived_zone[z]]
    return {'event':event,'metrics':{'requests':len(rows),'completed':completed,'active':sum(v['task'] is not None for v in vehicles),'expired':expired,'pending':len(pending),'completion_rate':completed/len(rows) if rows else 0,'worst_zone_completion_rate':min(ratios) if ratios else 0,'zone_service_gap':max(ratios)-min(ratios) if ratios else 0,'mean_pickup_wait_min':sum(wait)/len(wait) if wait else 0,'blocked_vehicle_min':blocked_min,'reposition_km':repositions*.5},'zones':[{'zone':z,'requests':arrived_zone[z],'completed':served_zone[z],'rate':served_zone[z]/arrived_zone[z] if arrived_zone[z] else None} for z in range(16)],'trace':trace}
def adversarial_search(city,rounds=3):
    rng=random.Random(314);candidates=[{'hotspot':rng.randrange(16),'edge':rng.randrange(len(edges(city))),'surge':5} for _ in range(12)];history=[]
    for iteration in range(rounds):
        scored=[]
        for event in candidates:
            runs=[simulate(city,12,'nearest',s,event,horizon=80) for s in (100,101)]
            loss=sum(1-r['metrics']['completion_rate']+.4*(1-r['metrics']['worst_zone_completion_rate']) for r in runs)/2
            scored.append((loss,event))
        scored.sort(key=lambda item:item[0],reverse=True);elite=scored[:3];history.append({'round':iteration,'best_loss':elite[0][0],'best_event':elite[0][1]})
        candidates=[dict(elite[0][1])]
        for _ in range(11):
            event=dict(rng.choice(elite)[1])
            if rng.random()<.7:event['hotspot']=rng.randrange(16)
            else:event['edge']=rng.randrange(len(edges(city)))
            candidates.append(event)
    return {'event':history[-1]['best_event'],'history':history,'search_seeds':[100,101],'method':'elite mutation search (12 candidates × 3 rounds); surrogate objective targets service failure, not a physical adversary'}
def cvar_loss(values,fraction=.25):
    ordered=sorted(values,reverse=True);tail=ordered[:max(1,math.ceil(len(ordered)*fraction))];return sum(tail)/len(tail)
def experiment():
    scenarios=[];searches={};demand_models={}
    for city in CITIES:
        search=adversarial_search(city);searches[city]=search;rates=learn_rates(city);demand_models[city]=rates
        for event_name,event in [('reference',{'hotspot':15,'edge':0,'surge':3}),('stress',search['event'])]:
            for fleet in (8,16):
                for policy in ('nearest','equity','robust'):
                    runs=[simulate(city,fleet,policy,s,event,rates) for s in (7,8,9,10)]
                    scenarios.append({'city':city,'event_name':event_name,'fleet':fleet,'policy':policy,'test_seeds':[7,8,9,10],'individual_metrics':[r['metrics'] for r in runs],'metrics':{**{k:sum(r['metrics'][k] for r in runs)/4 for k in runs[0]['metrics']},'cvar25_unserved':cvar_loss([1-r['metrics']['completion_rate'] for r in runs])},'trace_seed':7,'zones':runs[0]['zones'],'event':event,'trace':runs[0]['trace']})
    return {'synthetic':True,'scenarios':scenarios,'adversarial_search':searches,'learned_zone_rates':demand_models,'protocol':{'horizon_min':100,'edge_km':.5,'minutes_per_edge':1,'demand_train_seeds':list(range(100,110)),'scenario_search_seeds':[100,101],'test_seeds':[7,8,9,10],'fairness':'Geographic completion-rate disparity only; no demographic or protected-class data.','robust_policy':'One-step auction with district service deficit, trip length and known selected-edge disruption penalty; idle repositioning uses learned zone arrival rates. Not robust MPC or reinforcement learning.','event_knowledge':'All policies know current closures. Robust additionally knows which edge may close; this is an information advantage, not an isolated algorithm comparison.','search_eval_horizon':'Search uses 80 min; test uses 100 min. Stress is a discovered toy failure case, not a worst-case guarantee.'},'limitations':['All networks and demand are synthetic; no real emergency or equity outcomes validated.','Four test seeds provide weak tail-risk estimates; CVaR25 here is the worst single run.','Unfinished trips at the horizon count as active, not completed; compare within same horizon.','Auction is heuristic, not globally optimal; rates are simple count estimates.','No demographic fairness, causal validity or operational disaster-response claim.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='report.json');p.add_argument('--single',action='store_true');p.add_argument('--city',choices=CITIES,default='river');p.add_argument('--fleet',type=int,default=12);p.add_argument('--policy',choices=['nearest','equity','robust'],default='robust');p.add_argument('--seed',type=int,default=7);p.add_argument('--export-demand');args=p.parse_args()
    if args.export_demand:
        with Path(args.export_demand).open('w',newline='',encoding='utf-8') as handle:
            writer=csv.DictWriter(handle,fieldnames=['id','minute','origin','destination']);writer.writeheader();writer.writerows(demand(args.city,args.seed,{'hotspot':15,'edge':0,'surge':5}))
    result={'synthetic':True,**simulate(args.city,args.fleet,args.policy,args.seed,rates=learn_rates(args.city))} if args.single else experiment()
    Path(args.output).write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
