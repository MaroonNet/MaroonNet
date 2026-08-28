# MaroonNet

An offline, browser-based command post for volunteer Search & Rescue teams, built on Meshtastic
LoRa radios. MaroonNet turns the radios a team already carries into a search-effectiveness sensor:
live probability of detection per segment, predicted mesh coverage from terrain, and warnings about
the relay the mesh cannot afford to lose, all at a command post with no internet, feeding results
back to CalTopo.

> **Status: student capstone prototype.** MaroonNet is a University of Colorado Denver CS senior
> capstone (Fall 2026 – Spring 2027). It is intended for training and exercises. It is not certified
> for life-safety use and must not be relied on as a primary means of locating people.

## What it does

Field teams carry Meshtastic nodes that broadcast GPS positions over a LoRa mesh. A gateway node at
the command post connects to a laptop over USB. MaroonNet:

- shows the Incident Commander a live topographic map of every node, fully offline;
- computes coverage and probability of detection per search segment from the tracks, live, and ranks
  where the next team is worth the most;
- predicts where the mesh can and cannot be heard from the elevation model, and suggests relay
  placement;
- builds the live mesh topology from packet headers and flags critical relays;
- alerts when a node goes silent, with an inferred cause (power, range, congestion, stationary);
- pushes waypoints and messages to the field with logged ACK/NAK;
- provisions field nodes from the laptop with no CLI;
- imports CalTopo segments and exports tracks, sectors with POD, and the event log back to CalTopo;
- replays the whole mission for after-action review.

Everything runs from a single executable on Windows, macOS, or Linux. Meshtastic firmware is used
unmodified (pinned to 2.7.26).

## Repository layout

| Path         | Contents                                                                 |
| ------------ | ------------------------------------------------------------------------ |
| `maroonnet/`  | Python package: `bridge/` (serial daemon), `analytics/`, `api/` (FastAPI) |
| `dashboard/` | React + MapLibre GL JS frontend                                          |
| `tiles/`     | Planetiler vector-tile pipeline (OSM + USGS 3DEP contours)               |
| `spec/`      | Interface contracts: schema, WebSocket messages, REST endpoints          |
| `tests/`     | pytest suite                                                             |
| `hardware/`  | Bill of materials, wiring, antenna and range test logs                   |
| `docs/`      | Project Bible, decision log, standups, minutes, research, outreach       |

## Getting started (developers)

```bash
git clone https://github.com/<org>/maroonnet.git
cd maroonnet
uv sync --all-groups
uv run pytest -q
```

See `CONTRIBUTING.md` for the branch and review workflow and `docs/GITHUB_SETUP.md` for how the
repository is configured. If you use Claude Code, `CLAUDE.md` is loaded automatically.

## Team

Joshua "JJ" Wagner (Backend Lead, project lead), Corey Greene, Elijah Heimsoth, and Diego Alas,
advised by Professor David Ogle, University of Colorado Denver.

## License

GPL-3.0. See `LICENSE`. MaroonNet depends on the Meshtastic Python library and ecosystem, which are
GPL-3.0; the same license keeps the project compatible and keeps derivative work open.
