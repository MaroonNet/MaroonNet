# SPM — Sector Probability Mapping (MaroonNet)

SPM estimates where a lost person is likely to be found, as a probability
surface over the search area. (P)MP sums that surface per sector and draws it
as the heat map. This repo holds the model code, the case data pipeline and
the evaluation harness. See segment document SPM v1.1.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

spm harmonize        # downloads the free MapScore cases, validates, writes data/cases/cases.csv
spm evaluate         # scores uniform + ring models with leave-one-out, writes results/
pytest               # 29 tests: scorer, grid, cases, features, model contract, prior-art + hybrid (synthetic)
```

## What exists now (build step 1)

| Piece | File | What it does |
|---|---|---|
| Data contract | `src/spm/schema.py` | `Case` (one incident, any source) and `Prediction` (probability raster + mass outside the window). Everything speaks these two types. |
| Canonical grid | `src/spm/geodata/grid.py` | `Window`: square block of cells in the local UTM zone (EPSG:32613 for Colorado), origin snapped to the cell size so every layer lines up. |
| Scorer | `src/spm/eval/mapscore.py` | MapScore (Sava, Twardy, Koester & Sonwalkar 2016), re-implemented in numpy from the reference code. Random = 0, perfect ≈ 1. |
| Case pipeline | `src/spm/cases/` | One adapter per source → common schema → validation (duplicates, placeholders, bad coordinates) → `data/cases/cases.csv` plus `case_issues.csv` listing every exclusion. |
| Models | `src/spm/models/` | `uniform` (sanity baseline), `ring` (lognormal distance rings per category, fitted from training cases), `ring_pooled` (one ring for all categories). All follow `fit(cases)` / `predict(case, window)`. |
| Harness | `src/spm/eval/runner.py` | Refits each model per fold (leave-one-out or leave-one-region-out) and reports the mean MapScore with a bootstrap 95% CI. |

## First results (2026-09-24, free MapScore cases, leave-one-out, 25 m cells)

| model | cases | mean MapScore (95% CI) | median | mean, finds inside window only | finds outside 25 km window |
|---|---|---|---|---|---|
| uniform | 106 | −0.113 (−0.179, −0.057) | 0.000 | 0.000 | 12 |
| ring_pooled | 106 | 0.583 (0.477, 0.690) | 0.901 | 0.755 | 12 |
| ring | 106 | 0.595 (0.485, 0.701) | 0.900 | 0.753 | 12 |

How to read this:
* On finds inside the window, the ring model scores **0.75**. That is close to the published ring-model figure (0.78, Sava et al. 2016, 376 cases) and a third-party reproduction on this set (0.761). The scorer and ring model behave as expected.
* The overall mean is lower because **12 of 106 finds (11%) lie outside the 25 km window**. The window is searched first, so these score near −1. Deciding how large the window should be, and how much mass the model gives beyond it, is a real modeling decision.
* The per-category ring does not beat the pooled ring yet. Only `hiker` (50 cases) has enough cases to get its own fit; published Lost Person Behavior tables would fix that (see `configs/ring_quantiles.yaml`).
* Rerunning at MapScore's original 5 m cells gives the same result (0.595), so 25 m is a safe default.

## What the MapScore case set actually is

Checked against the repository on 2026-09-24:
* `case_in/input_unsorted.csv` has 131 rows, **all Arizona**. The README says the free cases also include New York and Yosemite; the files do not.
* 17 rows duplicate another case, 6 have the find equal to the IPP, and 2 have finds 278–370 km away. After validation, 106 cases remain. `data/cases/case_issues.csv` lists every exclusion.
* The `Distance` column does not match the coordinates in any consistent unit, so it is ignored and distance is recomputed from coordinates.
* The repository has **no LICENSE file**. The README says the cases are "free for distribution", so they are downloaded at build time, not committed here.
* The reference scorer reads the find cell as `values[x, y]` on a row-major array, which appears to transpose row and column. Ring maps are symmetric, so the published ring scores are unaffected. This implementation indexes `[row, col]`, and a test pins that down.

## Layout

```
configs/ring_quantiles.yaml     published ring distances (to be filled from Lost Person Behavior)
configs/prior_art.yaml          feature bins + published terrain multipliers (to be filled, with sources)
docs/ROADMAP.md                 phases, gates, experiments, data track
data/                           rebuilt by the CLI, never committed
results/                        score tables from `spm evaluate`, never committed
src/spm/
  schema.py                     Case, Prediction
  cli.py                        spm harmonize | evaluate
  cases/                        adapters/, categories.py, validate.py, harmonize.py
  geodata/grid.py               Window: CRS, snapping, distances
  geodata/stack.py              FeatureStack: terrain layers on a Window (builder = phase 3)
  geodata/synthetic.py          fake stacks for tests
  features/relative.py          relative terrain features (transfer between regions)
  features/spec.py              feature bins + published multipliers
  models/                       uniform, ring, bayes (prior-art), hybrid (learned, pooled)
  eval/                         mapscore.py, runner.py
  io/                           (step 3) raster + sector export for (P)MP
tests/                          fixtures/ + one test file per module
```

## Adding a data source

1. Create `src/spm/cases/adapters/<name>.py` with `NAME`, `fetch(dest)` and `load(src_dir) -> list[Case]`.
2. Map the source's category labels in a `CROSSWALK` dict. Keep the original in `category_raw`.
3. Register it in `ADAPTERS` in `cases/harmonize.py`, add a small fixture and a test.

Next in line: NYS DEC Forest Ranger missions (data.ny.gov `u6hu-h7p5`) and the Yosemite (YOSAR) ArcGIS layers.

## Roadmap

The full pathway (published models first, then the learned hybrid, then Colorado), with phases, exit gates, experiments and data requests: **[docs/ROADMAP.md](docs/ROADMAP.md)**.

1. ✅ Foundation: contract, grid, scorer, first adapter, ring baseline
2. Published numbers: ring tables from Lost Person Behavior, terrain multipliers from Jacobs/Doke (`configs/`)
3. More regions: YOSAR, NYS DEC adapters; data requests
4. Terrain stacks (3DEP, OSM + NPS trails, NHD, WBD, NLCD); export for (P)MP
5. Model A (prior-art) on real terrain: fall deliverable
6. Model B (learned hybrid) vs A on held-out regions
7. Colorado: pooled offset, out-of-range flags, RMNP reference cases

## Sources

* Sava, Twardy, Koester & Sonwalkar (2016), Evaluating lost person behavior models, *Transactions in GIS* 20(1):38–53, doi:10.1111/tgis.12143
* MapScore reference code and cases: https://github.com/ctwardy/mapscore
* Koester (2008), *Lost Person Behavior*, dbS Productions
