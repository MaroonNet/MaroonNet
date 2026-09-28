# AAR roadmap

Phases for the After Action Report segment, from AAR Architecture v1.0 section 11. Dates are the
team's and are not recorded here; schedule items are not decisions. Item numbers (Q-, F-, A-, R-,
C-, I-) are defined in the architecture document and in MaroonNet Architecture v1.0.

## Phase 0 — scaffold (this pull request)

- `aar/` package with the C-01 draft schema, store helpers, replay queries Q-01 to Q-05, a
  synthetic mission, and tests.
- `docs/architecture/maroonnet-aar-architecture-v1_0.md`.

Gate: pull request review.

## Phase 1 — contracts and rules

| Item | With | Needs |
| --- | --- | --- |
| C-01 mission store schema signed | Elijah ((P)MP), JJ (SPM); Diego confirms the packet fields | The store decision meeting: R-01 one store or several, R-02 engine, R-04 store shape |
| C-09 event record agreed | Elijah | The section 6.3 list as the AAR's proposal |
| R-11 retention rule written | Team | SAR practice; the IRB items on the team's list. Must exist before any real person's position is stored |
| A-02 gaps: derived or stored | Diego, Elijah | Where the quiet-node alert comes from |
| A-03 positions with no device time | Diego | How the firmware reports time without a fix |

Gate: C-01 signed.

## Phase 2 — build against the contracts

| Item | Needs |
| --- | --- |
| The daemon writes to the store on Diego's simulator (I-15); queries answer against real packet rows | C-01, C-08 radio pin, C-02 daemon messages |
| The AAR backend surface (endpoints or messages) | R-03 framework; A-01 scrub model |
| Replay UI: map, slider, one track; then selection (F-04), events (F-05), gaps (F-07) | R-10 map library; A-05 where the UI lives |
| Layer toggles (F-06) | The map library; C-04 surface format; sector versions from (P)MP |

Gate: one track replays with a slider in the shared frontend, from a store the daemon wrote.

## Phase 3 — integration and the vertical slice

Integration step 3 of MaroonNet Architecture v1.0 section 7.1: store to replay, on the slice's
region and mission, after step 1 (daemon to store to live view) and step 2 (inputs to SPM to heat
map).

Gate: the vertical slice (V-11).

## Later, not in the fall slice

- Coverage views: search radii (F-08), distance between searchers (F-09), per-sector coverage
  (F-10). Wait on the sweep-width team item (I-14).
- Charts (F-11), after the frontend pick.
- AAR export (F-12, U-03) and the history layer for the next search (I-19).
- Stripping the raw packet payload under the retention rule, if the team wants smaller files.

## Experiments the owner runs alongside

- A time-T query in a second engine, per AAR v1.1 section 7.
- A bundle-size and scrub-smoothness prototype against a synthetic mission, once the map library
  is picked (A-01).
