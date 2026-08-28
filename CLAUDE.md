# MaroonNet — Claude instructions

Single source of truth for how Claude works in this repo. Committed to git, loaded automatically by
Claude Code for every teammate; nobody keeps a private copy. Edit via pull request. Keep under 200 lines.

The **Project Bible** (`docs/bible/` once JJ commits it; v1.0 dated 2026-08-27) is the authority on
mission, scope, thesis, architecture, plan, and decisions. If this file and the Bible disagree, the
Bible wins and this file gets a fix-up PR. The signed Statement of Work is the scope authority until
SOW v3.0 is ratified. Known exception: Bible v1.0 calls the project "Marooned", a stale first-pass
name from an old source document. The working title is **MaroonNet**; the Bible gets that fix in v1.1.

## What this project is

MaroonNet is a CU Denver CS senior capstone (Fall 2026 – Spring 2027, EXPO in Spring 2027). It is an
open-source, **offline, browser-based command post for volunteer Search & Rescue teams** that plugs
directly into Meshtastic LoRa radios. It complements CalTopo (the tool Colorado teams standardize on);
it does not replace it.

The thesis: the mesh is a **sensor network**, not a map with dots. Three pillars plus two glue pieces:

1. Live probability of detection (POD) per search segment, computed from mesh GPS tracks.
2. Terrain-aware mesh coverage predicted from USGS 3DEP elevation (line-of-sight + link budget).
3. Mesh topology risk: articulation-point analysis flags the relay the mesh cannot afford to lose.
   Glue: CalTopo import/export, and mission replay of positions, coverage, alerts, and topology.

Also core: timeout alerting with five-class cause inference, bidirectional messaging with ACK/NAK
logging, field-node provisioning from the CP over USB, airtime budget, single-binary air-gapped boot.

Explicitly **not** in scope: firmware modifications, a phone app for field members, RSSI trilateration,
lost-person-behavior modeling (MaroonNet consumes POA and computes POD). Check Bible §5.2 before adding.

Team: JJ (Backend Lead, project lead), Corey (repo/git/CI/infra, outreach email), Elijah (SAR
technology research), Diego (meeting minutes, stand-ups). Frontend / Data & Infra / Integration-QA
role assignments are in Bible Ch. 15. Advisor: Prof. David Ogle.

## Repo layout

```
maroonnet/           Python package
  bridge/           serial bridge daemon: connect gateway node(s), decode, per-packet log
  analytics/        POD engine, terrain coverage, topology + articulation points, cause inference, airtime
  api/              FastAPI: REST, WebSocket push, static dashboard + tile serving, mission files
dashboard/          React + MapLibre GL JS frontend, built to static files served by the API
tiles/              Planetiler vector-tile pipeline (OSM + 3DEP contours), Colorado z10–16
spec/               Interface contracts: schema, WebSocket message types, REST endpoints (JJ owns)
tests/              pytest; hardware-in-the-loop tests marked `@pytest.mark.hardware`
hardware/           BOM, wiring, antenna and range test logs, gateway/field node setup
docs/               bible/, decisions/log.md, standups/, minutes/, research/, outreach/, GITHUB_SETUP.md
.github/            CI workflows, PR/issue templates, CODEOWNERS, ruleset JSON
```

Add any new top-level directory to this list in the same PR.

## Stack (locked in Bible §11.3 — do not propose alternatives without a decision-log entry)

- Python 3.12; `meshtastic` official Python library (pinned exact version) for all radio I/O;
  PyPubSub + asyncio in the bridge; numpy, Shapely, NetworkX for analytics; FastAPI + uvicorn.
- One SQLite file per mission. Append-only history tables; never UPDATE state rows in place.
- React + MapLibre GL JS dashboard; Planetiler MBTiles; 3DEP contours. Node/npm versions pinned,
  `package-lock.json` committed, install with `npm ci`.
- PyInstaller single binary built by GitHub Actions for Windows, macOS, Linux.
- Meshtastic firmware pinned to **2.7.26** on every node. No firmware changes. Do not upgrade mid-semester.
- Tooling: `uv` (envs + exact lock), `ruff` (lint + format), `pytest`, `pre-commit`.

## Commands

```
uv sync --all-groups                                  # install
uv run ruff check . && uv run ruff format --check .   # lint (CI job: lint)
uv run pytest -q                                      # tests (CI job: test)
uv run pytest -m hardware                             # only with a gateway node plugged in
uv run python -m maroonnet                             # run bridge + API locally (once main exists)
cd dashboard && npm ci && npm run dev                 # frontend dev server
```

Run lint and tests before every commit. If a command here is wrong, fix it here in the same PR.

## Git workflow (enforced by GitHub rulesets; do not work around them)

- `main` is protected and always deployable. No direct commits, including admins.
- Branch names: `feature/<short-desc>`, `fix/<short-desc>`, `chore/<short-desc>`, `docs/<short-desc>`.
  Branch from an up-to-date `main`. One feature per PR; merge within days, not weeks.
- A PR merges only with 2 approvals from teammates who did not author it, CI green, every review
  thread resolved, branch up to date with `main`. Squash-merge only; the PR title is the commit line.
- Any PR that touches an interface (schema, WebSocket message, REST endpoint, directory layout)
  updates `spec/` in the same PR. JJ reviews every interface change.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`. Imperative, <72 chars.
- Never commit secrets, `.env`, Meshtastic channel PSKs, node private keys, or a real person's
  location data. Real channel keys live on the devices and in a teammate's password manager.
- Never force-push a shared branch. Delete branches after merge.
- One person (Backend Lead) owns dependency updates, via dedicated `chore/deps-*` PRs.

## The cardinal rule (Bible §13.1)

**If the teammate cannot explain every line of a file to another team member from memory, it does
not get committed.** After generating code: the human reads every line, adds intent comments, renames
things to what they actually do, and refactors what they would have written differently. Claude's job
is to make that possible: small diffs, plain names, no cleverness, and an explanation of *why* with
every non-obvious choice. Prefer boring, well-documented libraries. A volunteer SAR team has to
maintain this after we graduate.

## Coding conventions

- Small, focused PRs; split anything over ~400 changed lines.
- Every new module gets a test; every bug fix gets a regression test. Hardware tests are marked.
- Type hints on all Python signatures. One-line docstrings on public functions.
- Two timestamps per row: device-reported time and CP receive time. Store UTC ISO-8601; order by CP
  time; display device time. Field clocks drift.
- Coordinates are WGS84 decimal degrees (lat, lon) as floats. Segment areas are planimetric m².
- Node identity is the Meshtastic node number. Team assignment is an event, not a column overwrite.
- Team types are data (foot, dog, vehicle, UAV); sweep width is a property of the type. Never
  hardcode "person".
- The per-packet log (Bible §11.6) is written for **every** received packet from day one, with
  relay_node, next_hop, hop_start, hop_limit, rx_snr, rx_rssi, want_ack, interface_id, raw + decoded.
  It cannot be reconstructed later. Do not "simplify" it.
- Never silently assume coverage in a track gap. Flag it; POD becomes "based on partial track".
- Log with `logging`, never `print`. WebSocket messages are JSON, snake_case, units in field names.
- Match the existing style of the file being edited. No unrelated reformatting in a PR.

## Mesh gotchas Claude must respect (Bible §10.2)

Traceroute is rate-limited to one per 30 s globally. DMs/probes/remote admin need the target's public
key in the CP NodeDB; provisioning and the radio check guarantee this; a missing key NAKs as
`NO_CHANNEL`. Payloads cap near 233 bytes (no polygons to field devices). Remote config writes reboot
the node; chain them in one transaction. Firmware throttles sends above 25% / 40% channel
utilization and scales intervals above 40 nodes: **silence is often normal**, and cause inference
must encode that. Minimum device-telemetry interval is 30 min.

## How Claude should behave here

- Before writing code: read the relevant Bible chapter, `spec/`, `docs/decisions/log.md`, and the
  closest existing module. Interfaces are decided before parallel work begins.
- State assumptions explicitly. Ambiguous requirement: ask one focused question. Teammate unavailable:
  choose the simplest option, say so in the PR body.
- Do not invent SAR operational facts. Anything about how real teams operate must trace to
  `docs/research/`, Bible Ch. 2–3, or a logged outreach conversation. Sweep-width numbers are
  placeholders until a practitioner reviews them; the UI labels POD as an estimate.
- Do not reopen settled questions (Bible Ch. 19 / `docs/decisions/log.md`) unless asked; if a change
  is warranted, propose a decision-log row with the reason.
- "Review" means: correctness, tests, secrets, timestamp/coordinate handling, append-only schema,
  spec compliance, airtime impact of anything that transmits. Rank by severity; no nit padding.
- Explain reasoning, not only conclusions. Pragmatic beats ideal.
- Never claim a test passed, a command ran, or a file exists without having done it.
- Tight responses. Code and diffs over prose. No emoji in code, commits, or docs.
- If a build/test command, directory, or convention changes, update this file in the same PR.

## Documentation conventions

- Tue/Thu meeting minutes: `docs/minutes/YYYY-MM-DD.md` (Diego). Weekly standup notes:
  `docs/standups/YYYY-MM-DD.md` (rotating note-taker, fixed agenda in Bible §14.4).
- Decisions: append a row to `docs/decisions/log.md` (date, decision, rationale).
- Outreach: `docs/outreach/log.md`, one row per organization. No personal phone/email in the repo.
- Terminology from the Bible glossary: IC, CP, segment, assignment, POA/POD/POS, coverage, sweep
  width, node, gateway, relay, articulation point, ACK/NAK. Not "squad leader"; not "ping" for a
  position packet.

## Safety and scope

- Position data of people in the field is sensitive: minimize what is stored, make retention
  explicit, never expose a network endpoint without auth.
- Student prototype for **training and exercises**, not operational missions, until a team decides
  otherwise. The UI, README, and every outreach message say so. Never promise field-to-field phone
  awareness or anything that requires reflashing radios.
