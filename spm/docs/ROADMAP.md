# SPM roadmap: from published models to a Colorado-ready learned model

*Proposed 2026-09-24. Phase months are a proposal; adjust them to the course calendar. Decisions go to the MaroonNet Decision Log, not here.*

## The idea in one paragraph

Two models are built one after the other. They share the same data, features and scoring.

- **Model A (prior-art):** the ring prior multiplied by published terrain multipliers. It needs no training and is built from Koester, Doke/Sava and Jacobs. It is the fall deliverable and the safety net.
- **Model B (learned hybrid):** starts from Model A's numbers and learns corrections from real cases. A Colorado-specific adjustment starts at zero and grows only as Colorado cases arrive.

Model B replaces Model A only if it scores higher on a region it never saw during training. The demo can therefore never get worse by trying B.

```
cases (AZ, YOSE, NY, ...) ─┐
                            ├─ relative features ─┬─ Model A: ring × published multipliers ─┐
terrain stacks (3DEP, OSM, ─┘   (same bins)       └─ Model B: ring × learned multipliers  ─┤
 NHD, WBD, NLCD)                                       (starts at A, pooled by region)      │
                                                                                            ▼
                                       MapScore, leave-one-out and leave-one-region-out ──► ship the better one
                                                                                            │
                                                  Colorado: region offset = 0, out-of-range cells flagged
```

## What is prior art and what is ours

| Published; we implement it | New; this project's contribution |
|---|---|
| Distance rings by category and ecoregion (Koester 2008) | Terrain multipliers *learned* from pooled open cases across regions |
| Watershed model (Doke 2012; Sava et al. 2016) | Leave-one-region-out test of whether learned multipliers transfer |
| Terrain multipliers near trails, roads, drainages (Jacobs 2015) | Regional partial pooling: a Colorado adjustment that starts at zero |
| Walking speed by slope (Tobler; Campbell et al.) | Out-of-range flags where the terrain is unlike anything in training |
| Behaviour mix for simulation (Hashimoto et al. 2022) | An offline tool for the command post |
| MapScore metric (Sava et al. 2016) | |

## Phases

### Phase 0: Foundation ✅ (done 2026-09-24)
- Data contract, canonical grid, MapScore scorer, MapScore case adapter, ring baseline.
- Result: on 106 Arizona cases the ring scores **0.753** on finds inside the window (published: 0.78). 12 finds fall outside the 25 km window.
- Code for the later phases already exists and is tested **on synthetic terrain only**: `FeatureStack`, relative features, Model A (`models/bayes.py`) and Model B (`models/hybrid.py`).

### Phase 1: Published numbers (October)
- [ ] Get *Lost Person Behavior* (dbS Productions, Internet Archive loan, or a local SAR team).
- [ ] Check the distance table transcribed in the MapScore repo (`arc-models/distance_by_category.py`, 72 rows, apparently miles) against the book, row by row. The row labels may be shifted by one. Enter the checked rows in `configs/ring_quantiles.yaml` with page numbers.
- [ ] Fill in `configs/prior_art.yaml` from Jacobs 2015 (trail, road and drainage multipliers by offset) and Doke/Sava (watershed), with a table or page reference for every number.
- [ ] Confirm which book ecoregion row applies to the Colorado Rockies (probably Dry domain, mountainous; verify on the book's map).
- [ ] **Decision D1:** window size, and how much probability sits beyond the window. At 25 km, 11% of Arizona finds fall outside.
- **Exit:** `spm evaluate --models ring,ring_published` runs, and every number in both configs has a source.

### Phase 2: More real cases (October to November, alongside Phase 1)
- [ ] YOSAR adapter (Doherty's ArcGIS open data, about 117 paired IPP and find locations).
- [ ] NYS DEC adapter. **First check** whether it has separate IPP and find coordinates. If it has only one point per incident, use it for category and time priors only.
- [ ] Send the data requests (see the data track below).
- [ ] **Decision D4:** choose one region as the **final exam**, held out and never looked at until Phase 5 is finished. Yosemite is the natural choice because it is the most mountainous.
- **Exit:** at least 2 regions of paired cases in `cases.csv`, and the leave-one-region-out split runs.

### Phase 3: Terrain stacks (November)
- [ ] Builder that produces a `FeatureStack` with the `BASE_LAYERS` names: 3DEP (dem), OSM plus NPS/USFS trails (trail_mask), roads, NHD (stream_mask), WBD HUC-12 (watershed_id), NLCD (landcover).
- [ ] Offline cache for the Rocky Mountain National Park region, plus on-demand pulls for training cases.
- [ ] `stack_provider(case, window)` for every training case. `evaluate(..., stack_provider=...)` already accepts it.
- [ ] Export the raster and per-sector JSON for (P)MP (`io/export.py`).
- **Exit:** every case has a stack, the RMNP stack loads with no network, and (P)MP displays a map.

### Phase 4: Model A on real terrain (December, the fall deliverable)
- [ ] Score `bayes` against `ring` with leave-one-out and leave-one-region-out (experiment E2).
- [ ] If a published multiplier makes scores worse, find out which one (drop one feature at a time) and report it.
- [ ] Demo: the RMNP reference case, with the find location shown on the heat map.
- **Gate A:** Model A scores at least as well as the ring, or you know exactly which multiplier hurts. Model A becomes the shipped model.

### Phase 5: Model B, the learned hybrid (January to February)
- [ ] **Decision D2:** freeze the feature list and bins in `prior_art.yaml` before fitting. No changes after looking at test results.
- [ ] Fit `HybridModel` on the real stacks, starting from Model A's values.
- [ ] Run experiments E3 to E5 (below). Open the final-exam region once, at the end.
- **Gate B:** Model B beats Model A on the held-out region(s) using paired per-case differences. If it doesn't, ship A and report the result: "the published weights are near what this much data supports."

### Phase 6: Colorado (March)
- [ ] Colorado cases use `region="US-CO"`. Their offset is zero until Colorado cases exist.
- [ ] Out-of-range flags (for example alpine tundra, talus, snow) are shown hatched in (P)MP.
- [ ] Reconstruct 3 to 10 RMNP cases from NPS news releases, marked as approximate, for a qualitative check.
- [ ] If county data arrives, it becomes the Colorado test set, and later training data for the Colorado offset.
- [ ] Team field day: GPS tracks of walking pace by slope and land cover on Colorado ground, feeding the travel-cost surface.

### Phase 7: Stretch
- Agent simulation: walker behaviour calibrated on other regions, run on Colorado terrain. Used for pretraining and demos only, never for testing.
- CNN only if real paired cases exceed about 1,000.

## Experiments

| ID | Question | Compare | Split | Phase |
|---|---|---|---|---|
| E1 | Do the published rings beat rings fitted to our own cases? | ring vs ring_published | LOO | 1 |
| E2 | Do the published terrain multipliers help on our cases? | bayes vs ring | LOO, LORO | 4 |
| E3 | Does learning beat the published multipliers on unseen regions? (**core result**) | hybrid vs bayes | LORO + final exam | 5 |
| E4 | Which features transfer between regions? (the question Doke asked) | hybrid with each feature dropped | LORO | 5 |
| E5 | How much regional pooling is right? | hybrid across a lam_region sweep | LORO | 5 |
| E6 | Does the Colorado map look sensible, and how much of it is flagged? | hybrid/bayes on RMNP cases | qualitative | 6 |

Compare models case by case (paired differences with a bootstrap CI), not mean against mean. With 100 to 300 cases, a model's mean MapScore has a CI of about ±0.1, but paired differences are much tighter.

## Data track (parallel; owners to assign)

| Request | To | Why |
|---|---|---|
| Code license; why the free set is Arizona-only | Charles Twardy (MapScore) | Permission to iterate on the code; the missing NY and Yosemite cases |
| YOSAR paired cases; license | Paul Doherty (CU Denver GES connection) | Mountain terrain; the best test region |
| De-identified find extract | Oregon OEM SAR coordinator | Largest source of find locations |
| FOIA request: ROMO SAR case reports (IPP and find fields) | NPS | Colorado cases; expect months |
| Data-sharing agreement | Larimer, Grand or Boulder county SAR / CSAR | A real Colorado test set |
| ISRID follow-up | Robert Koester (Corey) | Still the best source if it comes through |

## Decisions for the Decision Log

- **D1** Window size and mass beyond the window (Phase 1)
- **D2** Feature list and bins, frozen before Phase 5
- **D3** Book ecoregion row for Colorado
- **D4** Final-exam region, held out until the end
- **D5** Ship Model A or B (Gate B)

## Where the code is

| Piece | File | Status |
|---|---|---|
| Relative features | `src/spm/features/relative.py` | Built; tested on synthetic arrays |
| Feature bins and published values | `src/spm/features/spec.py`, `configs/prior_art.yaml` | Built; values blank until sourced |
| Terrain stack container | `src/spm/geodata/stack.py` | Built; the Phase 3 builder fills it |
| Synthetic terrain for tests | `src/spm/geodata/synthetic.py` | Built |
| Model A | `src/spm/models/bayes.py` | Built; equals the ring until the config is filled |
| Model B | `src/spm/models/hybrid.py` | Built; recovers a planted trail effect and beats the ring on an unseen synthetic region (synthetic only) |
