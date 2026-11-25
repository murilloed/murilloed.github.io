# TwinPulse · Calibrated digital twin

Real-data forecasting, measured uncertainty and road-capacity scenarios.

## Research hypothesis

Connect observed error to an auditable simulator: traffic prediction, calibrated intervals and capacity testing in one lab. The contribution is the experimental integration, not a new forecasting algorithm.

## Run

Python 3.10+, standard library only. From this directory:

```sh
python twinpulse.py --output report.json
python -m unittest discover -v
```

## Implementation

Ridge regression uses hour, weekday and previous-hour observed volume. A later period calibrates intervals; a still later period measures error and coverage. Forecasts drive a three-link corridor with vehicle conservation.

## Validation protocol

2,016 real counts; chronological training, calibration and test without shuffling. Compares ridge and persistence on 403 test observations and measures actual coverage, including when it falls below the 90% target.

## Data and units

Real counts: Hogue (2019), Metro Interstate Traffic Volume, UCI, DOI 10.24432/C5X60B. CC BY 4.0. Sample: last 2,016 available timestamps; duplicate weather rows removed by keeping the first. Missing hours are not imputed.

## Limitations

Real validation covers counts from one I-94 counter, not trips, fleets or interventions. Forecasts use observed lag: this is not a free-running multi-hour forecast. Queues, capacities and visual dots are hypothetical. Temporal dependence prevents a nominal-coverage guarantee.

## Next research step

Add multiple sensors, drift detection, adaptive temporal calibration and independent travel-time validation before infrastructure decisions.

No client endorsement or production performance claim. Consult the generated report for all model parameters, individual metrics and negative results. Browser demonstrations replay generated Python output.

## Data attribution and custom CSV

Code is MIT; `observed.csv` is adapted from Hogue (2019), UCI Metro Interstate Traffic Volume, DOI 10.24432/C5X60B, CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ . See DATA_SOURCE.json for sample transformations, upstream SHA256 and timestamp semantics. No endorsement by the data creator or MnDOT is implied.

`python fetch_data.py` rebuilds the attributed sample from the official UCI ZIP (network required only for this refresh). The archive already includes observed.csv for offline reproduction.

`python twinpulse.py --observed your.csv --output custom-report.json` accepts strictly increasing unique ISO timestamps and finite nonnegative volume counts (columns timestamp,volume; minimum 100 rows). Only adjacent observations exactly one hour apart form prediction pairs. This CLI evaluates counts; it does not prove causal validity of road-capacity changes. At least one hour of observed history is required per forecast. Temporal dependence/drift can reduce interval coverage below the nominal 90%.
