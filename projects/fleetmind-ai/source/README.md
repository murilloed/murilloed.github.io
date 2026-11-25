# FleetMind · AI & Simulation

Plataforma Python de frotas, demanda sintética, previsão e reposicionamento com IA.

Python platform for fleets, synthetic demand, forecasting and AI repositioning.

## Run / Executar

Python 3.10+, standard library only. Extract the archive and run from its directory:

```sh
python fleetmind.py --output report.json
python -m unittest discover -v
```

## Implementation

Discrete simulation of multiple vehicles and nonstationary Poisson requests across nine zones; queues, pickups, trips and expiration. Compares random dispatch, nearest available vehicle and shared-table Q-learning repositioning. L2 regression predicts demand counts by zone and minute.

## Evaluation

27 city, fleet and policy combinations, with three test seeds each. Q-learning trains on seeds 100–123; forecasting trains on 30–35 and evaluates on 70–72. Request balance and fleet conservation are tested. CSV compares observed and simulated counts using MAE/RMSE.

## Limitations

All published results use synthetic data. No real operational validation has been performed. Shared tabular Q-learning is exploratory and may lose to the baseline; it is not deep RL or an autonomous fleet. Topologies are stylized and inter-zone travel time is constant.

## Next steps

Integrate anonymized real requests and trips, calibrate travel times, expand agent state and compare policies using confidence intervals and out-of-distribution tests.

Independent research. All supplied data is synthetic. No client endorsement or real-world performance claim.

## Observed data

`python fleetmind.py --observed counts.csv --output validation.json`

CSV header: `minute,observed,simulated`. Unique, nonnegative integer minute keys and finite nonnegative counts. Align units, timezone, intervals and provenance before comparing. MAE/RMSE do not automatically calibrate the simulation. Q-learning trains on seeds 100–123 with fleet size 16. Test policies use the exact same request stream per seed (7/8/9). Demand forecasting uses separate synthetic seeds (30–35 train, 70–72 test). Each zone edge is 0.5 km and one minute; horizon 120 min; waiting requests expire after 12 min. Completed-request rate counts arrivals before the horizon; in-progress requests are reported separately. Shared Q table is an exploratory multi-agent coordination baseline with limited state, not a deployment-ready controller.

### Custom scenarios and request data

`python fleetmind.py --single --city commuter --fleet 8 --policy qlearning --seed 7 --export-demand demand.csv --output run.json`

`python fleetmind.py --requests requests.csv --fleet 16 --policy nearest --output observed-input-run.json`

Request CSV columns: `minute,origin,destination` (zones 0..8; origin differs from destination). Requests at minute 120 or later fall outside the current evaluation horizon. Imported data is labeled user supplied, with unverified provenance. The sample downloadable demand dataset is synthetic.
