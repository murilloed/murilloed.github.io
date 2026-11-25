"""GPS RouteLab: directed road graph, A*/Dijkstra and noisy GPS snapping. Stdlib only."""
import argparse
import heapq
import json
import math
import random
from pathlib import Path

def city(size=7, congestion=2.5):
    nodes = {y*size+x: (x, y) for y in range(size) for x in range(size)}
    edges = {n: [] for n in nodes}
    for n, (x,y) in nodes.items():
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx,yy=x+dx,y+dy
            if 0<=xx<size and 0<=yy<size:
                # Each block is 200 m; free-flow 40 km/h. Central corridor is congested.
                factor=congestion if y==size//2 and dy==0 else 1
                edges[n].append((yy*size+xx, 18*factor))
    return nodes,edges

def route(nodes, edges, start, goal, algorithm='astar', closed=None):
    if algorithm not in ('astar','dijkstra'): raise ValueError('unknown algorithm')
    if start not in nodes or goal not in nodes: raise ValueError('node outside graph')
    closed=set(closed or [])
    def h(n):
        x,y=nodes[n]; gx,gy=nodes[goal]
        return 18*(abs(x-gx)+abs(y-gy)) if algorithm=='astar' else 0
    queue=[(h(start),0,start)]
    costs={start:0}; previous={}; expanded=0
    while queue:
        _,cost,n=heapq.heappop(queue)
        if cost!=costs[n]: continue
        expanded+=1
        if n==goal:
            path=[n]
            while n in previous: n=previous[n];path.append(n)
            return {'path':path[::-1], 'travel_seconds':cost,'expanded':expanded}
        for v,weight in edges[n]:
            if (n,v) in closed: continue
            new=cost+weight
            if new<costs.get(v,float('inf')):
                costs[v]=new;previous[v]=n;heapq.heappush(queue,(new+h(v),new,v))
    return {'path':[], 'travel_seconds':None,'expanded':expanded}

def gps_experiment(seed=7, noise_m=35):
    rng=random.Random(seed);nodes,edges=city()
    result=route(nodes,edges,21,27)
    fixes=[]
    for truth in result['path']:
        x,y=nodes[truth]; px=x*200+rng.gauss(0,noise_m);py=y*200+rng.gauss(0,noise_m)
        nearest=min(nodes,key=lambda n:(nodes[n][0]*200-px)**2+(nodes[n][1]*200-py)**2)
        fixes.append({'true_node':truth,'matched_node':nearest,'lat':-15.80+py/111320,'lon':-47.9+px/(111320*math.cos(math.radians(-15.8))),'raw_error_m':math.hypot(px-x*200,py-y*200)})
    return {'seed':seed,'noise_m':noise_m,'synthetic':True,'fixes':fixes,'node_match_accuracy':sum(f['true_node']==f['matched_node'] for f in fixes)/len(fixes),'raw_rmse_m':math.sqrt(sum(f['raw_error_m']**2 for f in fixes)/len(fixes))}

def experiment():
    scenarios=[]
    for factor in (1,2.5,5):
        nodes,edges=city(congestion=factor)
        scenarios.append({'congestion':factor,**{a:route(nodes,edges,21,27,a) for a in ('astar','dijkstra')}})
    return {'synthetic':True,'block_m':200,'free_speed_kmh':40,'scenarios':scenarios,'gps':[gps_experiment(noise_m=n) for n in (15,60,140)],'limitations':['Synthetic grid, not a live street map or navigation service.','GPS fixes snap to nearest intersection, not HMM road-segment map matching.','A* lower bound assumes all edges take at least 18 seconds.','Coordinates are synthetic offsets near Brasilia; no measured GPS data.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='report.json');args=parser.parse_args()
    Path(args.output).write_text(json.dumps(experiment(),indent=2),encoding='utf-8')
