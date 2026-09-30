# AAR — After Action Report (MaroonNet)

The AAR is the mission, replayed. After a search, the commander scrubs through time on a map:
each radio's path draws as a trail, events sit on the timeline, searchers can be shown or hidden,
and out-of-range gaps are shown and never interpolated. This folder holds the backend side of that:
the draft mission store schema (contract C-01) and the replay queries over it. The replay UI lives
in the shared frontend once (P)MP picks it. See segment document AAR v1.1 and
**[docs/architecture/maroonnet-aar-architecture-v1_0.md](../docs/architecture/maroonnet-aar-architecture-v1_0.md)**.

> Everything in this package is a **draft**. The schema is proposed, not decided. Nothing here is
> in the Decision Log. The engine, the store shape, and the scrub model are open (architecture
> sections 5 and 7).

## Quick start

```bash
cd aar
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

aar synth --nodes 10 --hours 6 --interval 60           # writes data/synthetic/mission.sqlite
aar summary data/synthetic/mission.sqlite              # what it holds, and its out-of-range gaps
pytest                                                 # 16 tests: schema, replay queries, synthetic mission, CLI
```

No dependencies beyond the standard library. `sqlite3` ships with Python, so this runs anywhere;
it does not decide the engine question.

## What exists now (build step 0: scaffold)

| Piece | File | What it does |
|---|---|---|
| Schema draft | `src/aar/store/schema.sql` | Contract C-01 as proposed in the architecture, section 6: raw `packet` log (every MCM §3.2 field), typed `position` / `telemetry` / `message` rows, `event`, `sector` versions, `artifact` references. Two timestamps plus insert order. |
| Store | `src/aar/store/db.py` | Create a mission store (never overwrites), open one, and the append-only insert helpers a bridge daemon would call. |
| Replay queries | `src/aar/replay/queries.py` | Q-01 to Q-05 from architecture section 3: state at T, trails up to T, a time window, events up to T, gaps derived from consecutive device times. Plus the no-fix positions for A-03. |
| Synthetic mission | `src/aar/synthetic.py` | N radios on a random walk for H hours: delivery delay, out-of-range gaps, one report in a hundred with no device time, a few events. Deterministic per seed. No real person. |
| CLI | `src/aar/cli.py` | `aar synth` and `aar summary`. |
| Tests | `tests/` | One file per module. Hand-built mission with known answers for the queries. |

## How the queries answer the slider

At time T the slider needs every selected searcher's last known position (Q-01) and the trail
behind it (Q-02). Positions are drawn by **device time**, the radio's GPS time. Receive time is
kept beside it: the difference is the delivery delay, and a long jump between one radio's
consecutive device times is an out-of-range gap (Q-05), which the UI annotates and never fills in.
Whether these run on the server per slider move or once to build a bundle for the browser is
open (architecture section 7.1); the questions are the same either way.

## Layout

```
docs/ROADMAP.md               phases and gates for this segment
data/                         mission stores, local only, never committed
src/aar/
  store/schema.sql            C-01 draft
  store/db.py                 create, connect, insert helpers
  replay/queries.py           Q-01 .. Q-05, positions_without_fix
  synthetic.py                synthetic mission generator
  cli.py                      aar synth | aar summary
tests/                        test_store, test_replay, test_synthetic
```

Every folder carries `claude/` and `archive/` placeholders per the Team Claude Guide §3.3.

## Roadmap

The phases, what starts now, and what waits on which decision: **[docs/ROADMAP.md](docs/ROADMAP.md)**.

1. ✅ Scaffold: schema draft, store helpers, replay queries, synthetic mission, tests
2. C-01 signed by (P)MP and SPM; the C-09 event list agreed; the retention rule (R-11) written
3. The daemon writes to the store on the simulator; queries answer against real packet rows
4. Replay UI in the shared frontend: one track and a slider; then filters, events, gaps
5. Layers and coverage views (sweep widths are a team item)
6. Vertical slice: store to replay on the slice's region and mission

## Sources

* AAR v1.1 (segment document); MaroonNet Architecture v1.0; MCM v1.1 §3.2 and §6.8; (P)MP v1.1 §3.6 and §6.5
* Decision Log v1.1: V-03 (interactive AAR), V-10 (laptop-local), V-13 (no pre-mission role)
