# CarFlow · Dinâmica de carros

Microssimulação de carros, frenagem e ondas de congestionamento com IDM.

Car microsimulation, braking and traffic waves with IDM.

## Run / Executar

Python 3.10+, standard library only. Extract the archive and run from its directory:

```sh
python carflow.py --output report.json
python -m unittest discover -v
```

## Implementation

Intelligent Driver Model on a 1.2 km ring: each car adjusts acceleration using speed, net gap and leader-relative speed. 0.1 s integration and explicit overlap checks.

## Evaluation

Three densities, vehicle-count conservation, positive gaps and a density-versus-speed comparison. JavaScript uses the same equations and units as Python.

## Limitations

Single-lane ring with illustrative parameters. No junctions, lane changes, real sensors or empirical calibration. Flow is density × mean speed, not a detector count.

## Next steps

Calibrate IDM against observed trajectories, add traffic signals and validate spatial and temporal metrics on an urban network.

Independent research. All supplied data is synthetic. No client endorsement or real-world performance claim.
