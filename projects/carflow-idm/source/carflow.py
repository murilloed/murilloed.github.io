"""Single-lane periodic Intelligent Driver Model, explicit Euler, SI units."""
import argparse
import json
import math
from pathlib import Path

def simulate(cars=24, desired_kmh=80, duration=180, dt=.1, brake=True):
    if not isinstance(cars,int) or not 2<=cars<=80: raise ValueError('cars must be 2..80')
    if not 10<=desired_kmh<=120 or not 0<dt<=.2 or duration<=0: raise ValueError('invalid parameters')
    length=1200.;vehicle_length=4.5;v0=desired_kmh/3.6
    x=[i*length/cars for i in range(cars)];v=[min(v0,12.)]*cars
    speeds=[];trace=[];min_gap=float('inf');collision=False
    for tick in range(round(duration/dt)):
        t=tick*dt;acc=[]
        for i in range(cars):
            j=(i+1)%cars;gap=(x[j]-x[i])%length-vehicle_length
            min_gap=min(min_gap,gap)
            if gap<=0: collision=True;break
            desired=2+max(0,v[i]*1.5+v[i]*(v[i]-v[j])/(2*math.sqrt(1.2*2.)))
            a=1.2*(1-(v[i]/v0)**4-(desired/gap)**2)
            if brake and i==0 and 40<=t<44:a=min(a,-2.)
            acc.append(max(-9.,min(1.2,a)))
        if collision:break
        newv=[max(0,v[i]+acc[i]*dt) for i in range(cars)]
        # Explicit position update using average old/new speeds; never silently repair overlaps.
        displacement=[.5*(v[i]+newv[i])*dt for i in range(cars)]
        for i in range(cars):
            j=(i+1)%cars
            if (x[j]-x[i])%length-vehicle_length+displacement[j]-displacement[i]<=0:collision=True
        x=[(x[i]+displacement[i])%length for i in range(cars)];v=newv
        for i in range(cars):
            gap=(x[(i+1)%cars]-x[i])%length-vehicle_length
            if gap<=0 or .5*(v[i]+v[(i+1)%cars])*dt>length/cars:collision=True
            min_gap=min(min_gap,gap)
        if collision:break
        if tick%round(1/dt)==0:
            trace.append({'second':round(t,1),'positions':x[:],'speeds':v[:]})
        if t>=min(60,duration/3):speeds.extend(v)
    mean=sum(speeds)/len(speeds) if speeds else 0
    return {'synthetic':True,'parameters':{'cars':cars,'desired_kmh':desired_kmh,'duration_s':duration,'dt_s':dt,'ring_m':length,'brake_event':brake,'idm':{'a':1.2,'b':2,'T':1.5,'s0':2,'vehicle_length':4.5}},'metrics':{'mean_speed_kmh':mean*3.6,'flow_vehicles_hour':cars/length*mean*3600,'stopped_fraction':sum(s<1 for s in speeds)/len(speeds) if speeds else 0,'min_gap_m':min_gap,'collision':collision,'completed':not collision},'trace':trace}

def experiment():
    return {'synthetic':True,'scenarios':[simulate(cars=n) for n in (12,32,64)],'limitations':['Single-lane ring; no intersections, lane changing, vehicle sensors or autonomous driving stack.','IDM parameters are illustrative, not calibrated to observed trajectories.','Flow is a density × space-mean-speed estimate, not measured loop-detector throughput.','Collision checks invalidate a run; model is not a safety certification.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='report.json');p.add_argument('--cars',type=int);args=p.parse_args()
    Path(args.output).write_text(json.dumps(simulate(cars=args.cars) if args.cars else experiment(),indent=2),encoding='utf-8')
