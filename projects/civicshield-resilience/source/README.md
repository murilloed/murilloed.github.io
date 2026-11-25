# CivicShield · Resilient mobility

Adverse scenario generation and service auctions sensitive to geographic disparities.

## Research hypothesis

Search for failures before optimizing averages: an adversarial generator searches closure-and-demand combinations that degrade service. Policies are evaluated on both total completion and the least-served zone.

## Run

Python 3.10+, standard library only. From this directory:

```sh
python civicshield.py --output report.json
python -m unittest discover -v
```

## Implementation

Three distinct networks: grid, river with bridges and ladder corridor. Elite-mutation search chooses stress events on development seeds. A heuristic auction allocates vehicles; one variant adds zone service deficits, another adds disruption penalties and repositioning using learned demand rates.

## Validation protocol

36 configurations and 144 test runs. Events and rates use development seeds; tests use 7–10. Measures total completion, worst zone, geographic disparity and worst-seed loss. Paths respect closures and fleet size is conserved.

## Data and units

Synthetic topologies, requests and events; closure from minutes 30 to 64 and surge from minutes 30 to 59. One edge represents 0.5 km per minute. Learned demand rates are count estimates, not neural networks.

## Limitations

Synthetic data; geographic equity only, with no demographic data. CVaR25 with four seeds is only the worst run. The robust variant knows the event edge in advance: comparison includes an information advantage. Not robust MPC, RL or a validated public policy.

## Next research step

Validate against real demand and disruptions, expand tail samples, remove the information advantage in ablations and test optimization with explicit per-zone service constraints.

No client endorsement or production performance claim. Consult the generated report for all model parameters, individual metrics and negative results. Browser demonstrations replay generated Python output.

## Custom scenario

`python civicshield.py --single --city river --fleet 12 --policy robust --seed 42 --export-demand demand.csv --output custom-run.json`

`demand-sample.csv` contains generated requests (seed 7; river scenario with hotspot 15, edge 0 and surge 5). Columns: id,minute,origin,destination; zones 0..15. All requests in this sample are synthetic.

Policy definitions and experiment seeds are recorded in report.json. Imported real-world measurements are not included in this project. Calibrate and externally validate assumptions before applying results to a real fleet.
