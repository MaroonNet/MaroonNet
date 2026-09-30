# (P)MP roadmap

Phases for the (Pre)Mission Planning segment, from (P)MP Architecture v1.0 section 12. Dates are
the team's and are not recorded here; schedule items are not decisions. Item numbers (I-, C-, R-,
P-) are defined in MaroonNet Architecture v1.0; A- in AAR Architecture v1.0; M- in MCM
Architecture v1.0; PM- in the (P)MP architecture document.

## Phase 0 — folders, docs, and stubs (this pull request)

- `pmp/` package: subpackages per Architecture v1.0 section 5.1 (`api`, `daemon`, `planning`,
  `maps`, `web`) plus `contract/`; every module imports; every stub raises with the item it waits
  on; the C-02, C-03, and C-09 drafts as typed records; the C-05 manifest; `pmp status`; tests.
- `docs/architecture/maroonnet-pmp-architecture-v1_0.md`.

Gate: pull request review.

## Phase 1 — contracts and research

| Item | With | Needs |
| --- | --- | --- |
| C-03 mission input record and the category set (R-07, PM-03) | JJ | ISRID category definitions; what the model needs |
| C-05 terrain package draft, and one region built by hand (R-05, PM-04) | JJ signs; Diego signs | A Planetiler run on one small region; the reference case region (R-06) |
| C-06 coverage caller agreed; the split (R-08, M-05) | Diego | MCM's interface and baseline |
| C-02 message list agreed (PM-02) | Corey and Diego sign | Nothing; transport waits on R-03 |
| M-01 accepted as the daemon's input (MCM Architecture v1.0 section 10 question 9) | Diego | The `Bridge.on_record` stub against the synthetic feed |
| PM-01 one process or two | Corey | The store meeting (R-01, R-02, R-04) is the natural sitting |
| The framework bake-off (R-03): the same two endpoints in Flask, Django, FastAPI | Owner | A day of work; results in `docs/research/pmp/` |
| The map library comparison (R-10) | Owner | Offline vector tiles, large overlays, time-filtered layers, polygon editing; results in `docs/research/pmp/` |
| The Python-against-Node note (R-13) | Owner | (P)MP v1.1 section 6.1 |
| The two AAR asks on pull request #5: the C-09 list; one mission file | Owner answers | AAR Architecture v1.0 sections 5.2 and 6.3 |

Gate: R-03 and R-10 decided by the team; C-01 signed.

## Phase 2 — build against the contracts

| Item | Needs |
| --- | --- |
| The daemon consumes MCM's synthetic feed and writes the C-01 draft through `aar.store.db` | M-01 signed; C-01 signed; PM-01 |
| The API surface in the chosen framework; the C-02 transport | R-03 |
| The planning view in `pmp/web/`: map, heat map, sectors, assignments | R-10; C-04; A-05 (PM-06) |
| The terrain package for the slice region | R-05; R-06 |
| Radio spacing from team size, radio count, and the MCM node limit | I-14 (sweep widths) and the preset and interval field test (M-04) |
| Sector generation along terrain breaks | The terrain package; the sector research |

Gate: integration step 1 of Architecture v1.0 section 7.1, daemon to store to live view, on the
simulator.

## Phase 3 — integration and the vertical slice

Integration steps 2 and 4 of Architecture v1.0 section 7.1: inputs to SPM to heat map; the
coverage overlay on the map. Sectors and assignments on the screen; events to the store for
replay (step 3 is the AAR's).

Gate: the vertical slice (V-11).

## Later, not in the fall slice

- Radio configuration and provisioning from the web app (I-12, M-08; stretch goal 1, shared with MCM).
- Export and its scrubbing (R-15, U-03).
- Ranking (I-06), with continuous update.
- The history layer from a past search (I-19).

## Experiments the owner runs alongside

- The command shell measurement: memory and disk of a browser tab against Electron on the
  team's laptops ((P)MP v1.1 section 6.3).
- A Planetiler run on one small region, to learn the tooling before C-05 is written up.
