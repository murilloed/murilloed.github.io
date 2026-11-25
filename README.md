# murilloed.github.io

Personal academic and professional website of Murillo Edson de Carvalho Souza.

The site is bilingual (English and Portuguese), responsive, and designed for
publication with GitHub Pages at:

https://murilloed.github.io/

## Clients and institutional experience

The home page includes a logo panel linked to `#clients`. The bilingual gallery
lists the organizations and initiatives provided by the site owner, with research
and project initiatives identified separately. Entries without a confirmed visual
identity retain their names without a substitute logo.

Client brand assets are stored in `assets/clients/`; `sources.json` records their
origins. The marks remain the property of their respective owners. The avatar is
a local copy of the existing GitHub profile image.

## ML & AI Mobility

The `projects/temas/ml-ai-mobility/` gallery contains three independent executable
Python projects, with bilingual pages, interactive labs, source ZIPs and generated
reports. They also appear in the complete project gallery.

- `projects/gps-routelab/source/`: A*/Dijkstra routing and noisy synthetic GPS fixes.
- `projects/carflow-idm/source/`: single-lane IDM microsimulation, braking and density experiments.
- `projects/fleetmind-ai/source/`: seeded demand, fleet agents, dispatch baselines,
  shared tabular Q-learning, held-out demand regression and paired CSV validation.

All published runs use **synthetic data**. No real-city validation, autonomous
driving capability, client work or production performance is implied. The fleet
demo replays Python traces; routing and IDM calculate scenarios in the browser.
Fleet metrics average seeds 7/8/9; animations show seed 7 only. Each source README
documents reproduction commands and limitations. FleetMind supports importing a
request CSV and exporting generated demand; imported provenance remains unverified.

Run checks from the repository root:

```sh
python -m unittest discover -s projects/gps-routelab/source -v
python -m unittest discover -s projects/carflow-idm/source -v
python -m unittest discover -s projects/fleetmind-ai/source -v
node --test mobility.test.mjs
```

`python build_mobility.py` rebuilds these pages, artwork and source archives and
idempotently integrates topic links. It preserves the rest of the portfolio.
Regenerate the experiment reports by running each project's Python module before
rebuilding the pages. No external Python dependencies are needed (Python 3.10+).
The `mobility-checks.yml` workflow runs these checks on GitHub.
