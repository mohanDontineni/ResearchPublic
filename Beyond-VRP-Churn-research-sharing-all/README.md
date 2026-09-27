# Beyond VRP Churn: public reproducibility materials

This collection accompanies “Beyond VRP Churn: Exact Semantic Differencing for
Auditing RPKI Policy Changes.” It contains analysis code, frozen input identifiers,
measured outputs and figures for the September 1–14, 2026 cohort.

## Contents and boundaries

- `src/`: original analysis, independent checks, plotting code, and dependency locks.
- `data/`: acquisition manifests with public source URLs and SHA-256 checksums.
- `results/`: original measured outputs, witnesses, timings, and test log.
- `figures/`: original plotted images with non-image PNG metadata removed.
- `manifest.json` and `SHA256SUMS`: inventory of this exact downloaded collection.

No manuscript or manuscript-generation program is included. Private project
records, credentials, author contact details, integration scripts, raw provider
inputs, and third-party paper PDFs are excluded. This collection does not establish
journal acceptance, a DOI deposit, or independent reproduction by a third party.

Core code and result files are byte-for-byte copies of the executed study artifact.
The README and sharing notes were prepared for this collection; PNG metadata was
removed without changing the stored image-data chunks. OpenAI Codex assisted with
research development and the original analysis code. These materials do not assign
authorship to an AI system.

## Reproduce the experiments

Extract the complete bundle into a new directory. Work from its root. The core
analysis uses Python's standard library; the recorded environment was CPython
3.14.4 on Linux x86-64. Preserve the bundled results before running because the
programs overwrite output files. Actual runtime and memory use depend on hardware.

```sh
mkdir -p data results figures
python3 src/test_semantic.py
python3 src/fetch_frozen.py
python3 src/verify_inputs.py
python3 src/run_cohort.py
python3 src/project_routes.py
python3 src/benchmark.py
python3 src/inspect_case.py
python3 src/summarize.py
```

The frozen downloader obtains the 70 RPKI components and two prefix-to-AS tables
identified in `data/input-manifest.json`, verifies their recorded hashes, and
assembles the daily views. A mismatch fails rather than silently replacing an
input. Downloads require network access and sufficient local storage. The analysis
is offline after acquiring those files. Obtain inputs under their providers' terms.

For the independent check, use Node.js 22:

```sh
mkdir -p validator
cp src/validator-package.json validator/package.json
cp src/validator-package-lock.json validator/package-lock.json
npm ci --prefix validator --ignore-scripts
NODE_PATH="$PWD/validator/node_modules" node src/third_party.cjs
```

This uses local VRPs, not a live validation service. It checks all 575 changed route
pairs under both views; it does not validate every stable pair or the original
certificate chains.

To rebuild figures in an isolated Python environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-figures.txt
.venv/bin/python src/plot_results.py
```

## Interpret the outputs

`cohort.csv` summarizes 13 daily transitions and seven prefix-length caps.
`cohort.json` retains per-origin and per-length detail. Witness files contain
concrete members of computed differences checked by the ancestor validator.
`route-projection.json` classifies a fixed set of routes under two views: these are
not observed BGP events. `benchmark.json` times the authorization kernel only;
ratios must not be described as end-to-end speedups. `summary.json` summarizes the
recorded results. `illustrative-case.json` is a case chosen after inspecting the
cohort, not a prespecified outcome. Public routing identifiers do not establish
operator error, malicious intent, or route legitimacy.

## Data sources and reuse

RPKI components: RIPE NCC RPKI archive, https://ftp.ripe.net/rpki/ .
Route inputs: CAIDA UCSD Routeviews Prefix to AS mappings Dataset for IPv4 and IPv6,
September 14, 2026, https://www.caida.org/catalog/datasets/routeviews-prefix2as/ .
See the manifests for exact URLs, retrieval times, and checksums.

Original provider data are not redistributed. Provider and dependency licenses
continue to apply; this collection grants no license over third-party materials.
No new blanket software license is asserted by packaging these files. Publications
using the CAIDA dataset must follow its attribution and reporting terms. No report
has been sent to CAIDA by this packaging step.
