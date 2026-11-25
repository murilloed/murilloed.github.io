# VoltSwarm · Fleets and energy

Electric-vehicle agents coordinate trips and charging under infrastructure failures.

## Research hypothesis

Treat energy, charging queues and passenger demand as a coupled problem. Explore when explicit charging coordination is more useful than choosing the nearest charger or learning only from historical durations.

## Run

Python 3.10+, standard library only. From this directory:

```sh
python voltswarm.py --output report.json
python -m unittest discover -v
```

## Implementation

Vehicles move across a 16-zone grid, consume energy per edge and must retain enough energy to reach a charger after each trip. Compares nearest charger, reservation-based queue prediction and a contextual bandit learning time to finish charging.

## Validation protocol

18 configurations, 54 test runs. Bandit trains on seeds 100–111 with fleet 16; evaluates on seeds 7–9 with fleets 12/24. Measures service, queues, energy, minimum battery and energy balance; includes a station outage in the storm scenario.

## Data and units

Synthetic data and infrastructure. Each edge is 0.8 km and takes one minute; 30 kW charger per port. Station 7 is unavailable from minutes 65 to 104. No hardware is controlled.

## Limitations

Synthetic micro-EV simulation with a 12 kWh battery. No real charging sessions, electrochemical model or grid power flow. Bandit is not deep RL; unfinished charging decisions do not update estimates, potentially causing bias.

## Next research step

Calibrate consumption using real telemetry and charging sessions; add tariffs, degradation and electrical limits. Test multi-agent learning with out-of-distribution evaluation and fair ablations.

No client endorsement or production performance claim. Consult the generated report for all model parameters, individual metrics and negative results. Browser demonstrations replay generated Python output.

## Custom scenario

`python voltswarm.py --single --city storm --fleet 12 --policy reservation --seed 42 --export-demand demand.csv --output custom-run.json`

`demand-sample.csv` contains generated requests (seed 7; balanced EV scenario). Columns: id,minute,origin,destination; zones 0..15. All requests in this sample are synthetic.

Policy definitions and experiment seeds are recorded in report.json. Imported real-world measurements are not included in this project. Calibrate and externally validate assumptions before applying results to a real fleet.
