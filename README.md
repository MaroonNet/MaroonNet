# MaroonNet

Open-source location tracking, logging, and after-action replay for Search & Rescue teams operating
beyond cell service. Built on LoRa / Meshtastic mesh radios.

> **Status: student prototype.** MaroonNet is a University of Colorado Denver senior capstone project
> (Fall 2026 – Spring 2027). It is not certified for life-safety use. Do not rely on it as a primary
> means of locating people.

## The idea

Searchers carry small LoRa radios running Meshtastic. Each radio periodically broadcasts its GPS
position and a timestamp across the mesh. A base-station node at the incident command post receives
those pings, and MaroonNet:

1. stores every ping in a database,
2. shows the Squad Leader a live browser map of where every searcher is right now, and
3. after the operation, replays the stored tracks as a timelapse and coverage map so the team can see
   what ground was actually covered and what was missed, for After Action Reports.

Stretch goal: mesh nodes carried by drones to extend coverage over ridgelines and drainages.

## Repository layout

| Directory   | Contents                                                              |
| ----------- | --------------------------------------------------------------------- |
| `firmware/` | Meshtastic device configuration, channel presets, node role settings  |
| `backend/`  | Ingest service (mesh to database), API, replay generation             |
| `web/`      | Browser map UI for live view and AAR replay                           |
| `hardware/` | Bill of materials, wiring, enclosures, antenna and range test logs    |
| `docs/`     | Architecture decisions, meeting minutes, research, outreach log       |

## Getting started

```bash
git clone https://github.com/<org-or-user>/MaroonNet.git
cd MaroonNet
uv sync
uv run pytest
```

See `CONTRIBUTING.md` for the branch and review workflow, and `CLAUDE.md` if you are using Claude Code
on this repo.

## Team

Corey Greene, Elijah Heimsoth, Joshua "JJ" Wagner, and Diego Alas, advised by Professor David Ogle,
University of Colorado Denver.

## License

GPL-3.0. See `LICENSE`. MaroonNet depends on the Meshtastic ecosystem, which is GPL-3.0 licensed;
using the same license keeps the project compatible and keeps derivative work open.
