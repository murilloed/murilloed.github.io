"""Forecast-calibrated aggregate traffic twin. Standard-library implementation."""
import argparse
import csv
import datetime as dt
import json
import math
import random
from pathlib import Path

def load(path):
    with Path(path).open(encoding='utf-8-sig') as handle:rows=list(csv.DictReader(handle))
    output=[]
    for row in rows:
        t=dt.datetime.fromisoformat(row['timestamp']);volume=float(row['volume'])
        if not math.isfinite(volume) or volume<0:raise ValueError('volume must be finite and nonnegative')
        output.append((t,volume))
    if len(output)<100 or any(b[0]<=a[0] for a,b in zip(output,output[1:])):raise ValueError('need >=100 strictly ordered unique observations')
    return output
def features(timestamp,lag):return [1.]+[float(timestamp.hour==i) for i in range(24)]+[float(timestamp.weekday()==i) for i in range(7)]+[lag/1000]
def solve(matrix,vector):
    a=[list(row)+[v] for row,v in zip(matrix,vector)];n=len(a)
    for i in range(n):
        pivot=max(range(i,n),key=lambda j:abs(a[j][i]));a[i],a[pivot]=a[pivot],a[i]
        d=a[i][i]
        if abs(d)<1e-12:raise ValueError('singular system')
        a[i]=[v/d for v in a[i]]
        for j in range(n):
            if j==i:continue
            factor=a[j][i];a[j]=[x-factor*y for x,y in zip(a[j],a[i])]
    return [row[-1] for row in a]
def fit(rows):
    n=33;matrix=[[0.]*n for _ in range(n)];vector=[0.]*n
    for t,lag,target in rows:
        x=features(t,lag)
        for i in range(n):
            vector[i]+=x[i]*target/1000
            for j in range(n):matrix[i][j]+=x[i]*x[j]
    for i in range(n):matrix[i][i]+=1.
    return solve(matrix,vector)
def predict(weights,t,lag):return max(0,1000*sum(a*b for a,b in zip(weights,features(t,lag))))
def quantile(errors,alpha=.1):
    if not errors:raise ValueError('empty calibration')
    ordered=sorted(errors);return ordered[min(len(ordered)-1,math.ceil((len(ordered)+1)*(1-alpha))-1)]
def scores(records):
    e=[r['predicted']-r['observed'] for r in records]
    return {'mae':sum(abs(v) for v in e)/len(e),'rmse':math.sqrt(sum(v*v for v in e)/len(e)),'coverage':sum(r['lower']<=r['observed']<=r['upper'] for r in records)/len(records),'mean_interval_width':sum(r['upper']-r['lower'] for r in records)/len(records)}
def queue_rollout(records,capacity=3200,seed=7):
    """Stylized 3-link finite-capacity corridor; measured counts drive arrivals."""
    rng=random.Random(seed);queues=[0,0,0];trace=[];entered=0;exited=0;vehicle_id=0
    # Each record becomes one hour; per-link capacity is vehicles/hour.
    for record in records[-48:]:
        arrivals=round(record['predicted']);entered+=arrivals;queues[0]+=arrivals
        old=queues[:];depart=[min(old[i],capacity) for i in range(3)]
        queues=[old[0]-depart[0],old[1]-depart[1]+depart[0],old[2]-depart[2]+depart[1]];exited+=depart[2]
        particles=[]
        for link,q in enumerate(queues):
            for _ in range(min(12,math.ceil(q/300))):particles.append({'id':vehicle_id,'link':link,'progress':round(rng.random(),3)});vehicle_id+=1
        assert entered==exited+sum(queues)
        trace.append({'timestamp':record['timestamp'],'queues':queues[:],'arrivals':arrivals,'exited_total':exited,'entered_total':entered,'particles':particles})
    return {'capacity_per_link_vph':capacity,'trace':trace,'metrics':{'entered':entered,'exited':exited,'queued':sum(queues),'peak_queue':max(sum(t['queues']) for t in trace)},'synthetic_movement':True}
def experiment(path):
    observed=load(path)
    rows=[(t,old[1],v) for old,(t,v) in zip(observed,observed[1:]) if t-old[0]==dt.timedelta(hours=1)]
    if len(rows)<50:raise ValueError('need at least 50 adjacent one-hour prediction pairs')
    a=int(.6*len(rows));b=int(.8*len(rows));train,cal,test=rows[:a],rows[a:b],rows[b:]
    weights=fit(train);models=[]
    for model in ('persistence','ridge'):
        forecast=lambda t,lag:lag if model=='persistence' else predict(weights,t,lag)
        radius=quantile([abs(forecast(t,lag)-v) for t,lag,v in cal])
        records=[]
        for t,lag,v in test:
            p=forecast(t,lag);records.append({'timestamp':t.isoformat(sep=' '),'observed':v,'predicted':p,'lower':max(0,p-radius),'upper':p+radius})
        models.append({'model':model,'radius':radius,'metrics':scores(records),'records':records,'corridors':[queue_rollout(records,c) for c in (2400,3200,4000)]})
    return {'observed_data':True,'validation_scope':'One-step-ahead aggregate hourly traffic counts only. Lag at t-1 is observed; not an open-loop multi-hour forecast. Synthetic vehicle paths and capacity interventions are not empirically validated.','protocol':{'train_n':len(train),'calibration_n':len(cal),'test_n':len(test),'train_end':train[-1][0].isoformat(),'calibration_start':cal[0][0].isoformat(),'calibration_end':cal[-1][0].isoformat(),'test_start':test[0][0].isoformat(),'test_end':test[-1][0].isoformat(),'excluded_nonhourly_pairs':len(observed)-1-len(rows),'target_coverage':.9,'features':'hour one-hot, weekday one-hot, observed previous-hour volume','fit':'ridge normal equations, L2=1, train only','interval':'absolute residual quantile on separate calibration period; no time-series coverage guarantee'},'ridge_weights':weights,'models':models,'limitations':['Single traffic counter, no fleet trajectories or measured travel-time validation.','Chronological split is small and location specific.','Temporal dependence and drift can invalidate nominal conformal coverage.','Corridor capacity is illustrative; no causal claim about changing infrastructure.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observed',default=str(Path(__file__).with_name('observed.csv')));p.add_argument('--output',default='report.json');args=p.parse_args()
    Path(args.output).write_text(json.dumps(experiment(args.observed),separators=(',',':')),encoding='utf-8')
