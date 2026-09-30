# MCM roadmap

Phases for the Mesh Connectivity Map segment, from MCM Architecture v1.0 section 11. Dates are the
team's and are not recorded here; schedule items are not decisions. Item numbers (M-, A-, C-, I-,
R-) are defined in the architecture documents.

## Phase 0 — scaffold (this pull request)

- `mcm/` package: the M-01 radio record, the normalizer, the gateway (serial), the radio profile
  with an empty firmware pin, airtime math, the gap definition, the coverage interface with a
  free-space baseline, the field message set, field warnings, a synthetic feed, and tests.
- `mcm/docs/maroonnet-mcm-architecture-v1_0.md` (inside the package for now; may move to
  `docs/architecture/` beside the AAR document later).

Gate: pull request review.

## Phase 1 — pin and confirm

| Item | With | Needs |
| --- | --- | --- |
| C-08 firmware pin recorded in `configs/radio_profile.toml` | JJ (hardware custodian) | Release notes for the two or three latest stable releases; a bench test on the Heltec V3 boards |
| A real capture replaces the hand-built fixtures | JJ | The pin; one bench session |
| M-01 confirmed against the daemon and the C-01 draft | Elijah (daemon), Corey (C-01) | The field mapping in architecture section 4.3 |
| A-02 gaps: derived or stored | Corey, Elijah | Architecture section 5 |
| A-03 positions with no device time | Corey | The capture above: what the firmware sends without a fix |

Gate: M-01 confirmed and the firmware pinned.

## Phase 2 — the daemon on a simulator

| Item | Needs |
| --- | --- |
| `meshtasticd` running on a laptop (sim tier 2); TCP transport in the gateway | Research; the pin |
| The daemon consumes `Gateway` records and writes the C-01 draft | Phase 1; Elijah's daemon |
| Quiet-node alert on the (P)MP screen from `QuietNodeWatch` | A-02; C-02 |
| Meshtasticator trial (sim tier 3) | Research |

Gate: a synthetic mission flows simulator to daemon to store to live view.

## Phase 3 — field test and the vertical slice

- Preset and interval from a field test in local terrain, with the node count the team needs
  (architecture section 6.2).
- Coverage model: elevation, line of sight, Fresnel, foliage, per MCM v1.1 section 6.4, with the
  split agreed with (P)MP; validation against SPLAT! and against observed reception.
- Integration step 1 of MaroonNet Architecture v1.0: radios to daemon to store to live view.

Gate: the vertical slice (V-11).

## Later, not in the fall slice

- Custom field app and the non-stock message types (sector assignment, warnings on the phone).
- Radio configuration and provisioning from the web app (segment stretch goal 1, with (P)MP).
- MQTT or multi-gateway transport; range extension modeling (pole, backpack, drone).
