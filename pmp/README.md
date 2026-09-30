# (P)MP — (Pre)Mission Planning (MaroonNet)

(P)MP is the commander's setup and the command post screen. The commander opens the application
on a laptop, loads maps, enters what is known about the missing person, and starts the mission.
The screen stays in use through the whole mission. This folder holds the backend side of that:
the bridge daemon (group-shared), the plan (sectors, assignment, radio spacing), the terrain
package, and (P)MP's drafts of the contracts it writes. The frontend waits on the map library
pick (R-10). See segment document (P)MP v1.1 and
**[docs/architecture/maroonnet-pmp-architecture-v1_0.md](../docs/architecture/maroonnet-pmp-architecture-v1_0.md)**.

> Everything in this package is a **draft**, and phase 0 is **stubs**: every module imports, each
> function carries its signature and raises `NotImplementedError` with the item it waits on, and
> the contract records are typed dataclasses with validation and serialization only. Nothing here
> is in the Decision Log.
> The backend framework (R-03), the map library (R-10), and the command post process shape
> (PM-01) are open.

## Quick start

```bash
cd pmp
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

pmp status                                             # what exists, what each piece waits on
pytest                                                 # 59 tests: imports, stubs, contract round-trips
```

No dependencies beyond the standard library. Nothing here imports `spm`, `aar`, or `mcm`; the
daemon reads MCM's record by field name and writes through store helpers handed to it.

## What exists now (phase 0: folders, docs, and stubs)

| Piece | File | What it does |
|---|---|---|
| C-02 draft | `src/pmp/contract/messages.py` | `DaemonMessage`: what the daemon pushes to the screen (`node_seen`, `position`, `telemetry`, `message`, `quiet_node`, `gap`, `mission`), with host time and a sequence number. Transport waits on R-03. |
| C-03 draft | `src/pmp/contract/mission_input.py` | `MissionInput`: last known position and time, or the no-known-position case with hours elapsed; subject category (values Open, R-07); team size; radio count. Mapping to SPM's `Case` documented, not built. |
| C-09 draft | `src/pmp/contract/events.py` | `Event` in the shape of the C-01 `event` row; the AAR's type list mirrored and marked Open; `OverridePayload` per (P)MP v1.1 section 6.5. |
| Bridge daemon | `src/pmp/daemon/bridge.py` | `Bridge.on_record` (the M-01 callback), `run` (asyncio), `row_from_record` (C-01 mapping by name). Stubs. Group-shared: second sign-off. |
| Outbound | `src/pmp/daemon/outbound.py` | `send_text`, `send_waypoint` through MCM's `Gateway`. Stubs. |
| API surface | `src/pmp/api/surface.py` | The calls the screen makes, as plain functions, and the `SURFACE` table. Framework-neutral. Stubs. |
| Planning | `src/pmp/planning/` | `Sector`, `Assignment`, `SpacingPlan` records; generate, split, merge, assign, spacing, and the C-06 coverage call. Stubs. |
| Terrain package | `src/pmp/maps/package.py` | C-05 draft: `TerrainPackage` manifest (region, bbox, CRS, cell size, layers with checksums). `region.py`: the select-a-region step and the Planetiler run. Stubs. |
| CLI | `src/pmp/cli.py` | `pmp status`. |
| Tests | `tests/` | Every module imports; every stub raises with a reason; the contract records round-trip through dict and JSON. |

## Layout

```
docs/ROADMAP.md               phases and gates for this segment
data/                         terrain packages and mission stores, local only, never committed
web/                          frontend placeholder (R-10, A-05)
src/pmp/
  contract/                   messages.py (C-02), mission_input.py (C-03), events.py (C-09)
  daemon/                     bridge.py, outbound.py            group-shared, second sign-off
  api/surface.py              the endpoints and pushes, framework-neutral
  planning/                   sectors.py, assignment.py, spacing.py, coverage.py
  maps/                       package.py (C-05), region.py
  cli.py                      pmp status
tests/                        test_imports, test_contracts
```

Every folder carries `claude/` and `archive/` placeholders per the Team Claude Guide §3.3.

## Roadmap

The phases, what starts now, and what waits on which decision: **[docs/ROADMAP.md](docs/ROADMAP.md)**.

1. Phase 0 (done, this pull request): folders, docs, stubs, contract drafts, this README
2. Contracts and research: C-03 with JJ; C-05 draft and one region built; C-06 caller with Diego; the framework bake-off and the map comparison in `docs/research/pmp/`; PM-01 with Corey
3. Build against the contracts: the daemon on the synthetic feed writing the C-01 draft; the API in the chosen framework; the planning view; the terrain package for the slice region
4. Integration: daemon to store to live view; inputs to SPM to heat map; coverage overlay
5. Vertical slice (V-11)

## Sources

* (P)MP v1.1 (segment document); MaroonNet Architecture v1.0 §2.3, §3, §4, §5.1, §6, §7
* AAR Architecture v1.0 §5, §6, §8 (pull request #5); MCM Architecture v1.0 §4, §6, §8 (pull request #6); SPM v1.1 §2 and `spm/src/spm/schema.py` (pull request #4)
* Decision Log v1.1: V-02 (static surface), V-10 (laptop-local), V-13 (map and tile loading is (P)MP)
