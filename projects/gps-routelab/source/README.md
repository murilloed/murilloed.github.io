# GPS RouteLab

Roteamento A*, trânsito e associação de posições GPS à rede viária.

A* routing, traffic and GPS-to-road-network matching.

## Run / Executar

Python 3.10+, standard library only. Extract the archive and run from its directory:

```sh
python gps_routelab.py --output report.json
python -m unittest discover -v
```

## Implementation

Directed 49-intersection graph; costs in seconds; A* with an admissible lower bound and Dijkstra reference; road closure; Gaussian noise and nearest-intersection matching.

## Evaluation

A* versus Dijkstra cost comparison across traffic scenarios, closure tests and GPS evaluation at three noise levels. The report records synthetic fixes and their errors.

## Limitations

Not a navigation service or satellite capture. Grid and coordinates are synthetic; nearest-intersection matching does not replace HMM map matching on real roads.

## Next steps

Import OpenStreetMap and anonymized trajectories; match fixes to road segments and compare probabilistic methods.

Independent research. All supplied data is synthetic. No client endorsement or real-world performance claim.
