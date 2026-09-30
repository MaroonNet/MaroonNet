# MaroonNet — Claude instructions

This file is the single source of truth for how Claude works on this repo. It is committed to git and
loaded automatically by Claude Code for every teammate, so nobody should keep a private copy.
Edit it through a normal pull request, like any other file. Keep it under 200 lines.

## What this project is

MaroonNet is a CU Denver senior capstone (Fall 2026 – Spring 2027, presenting at the Spring 2027 EXPO).
It is an open-source location management, tracking, and logging system for Search & Rescue (SAR) teams
operating where there is no cell service.

- Field searchers carry LoRa / Meshtastic radios that broadcast GPS position + timestamp over the mesh.
- A base-station node feeds those pings into a backend, which stores them in a database.
- A browser-based map shows the Squad Leader live searcher positions over the search area.
- After the operation, the stored track data rebuilds the search as a timelapse / coverage map for
  After Action Reports (think "Hero's Path" in Breath of the Wild) so missed areas are visible.
- Stretch goal: drones carrying mesh nodes to extend range.

Team: Corey (repo/git/infra, outreach email), JJ (documentation, outreach calls, hardware custodian),
Elijah (SAR technology research), Diego (meeting minutes, stand-ups). Advisor: Prof. David Ogle.

## Repo layout

```
firmware/   Meshtastic device configs, channel presets, any custom node firmware
backend/    Ingest service (mesh -> DB), API, replay/timelapse generation
web/        Browser map UI (live view + AAR replay)
spm/        Sector Probability Mapping: lost-person probability rasters, models, MapScore eval
hardware/   Bill of materials, wiring, enclosure notes, antenna/range test logs
docs/       ADRs, meeting minutes, research, outreach log, EXPO material
.github/    CI workflows, PR/issue templates, CODEOWNERS
```

If you create a new top-level directory, add it to this list in the same PR.

## Stack (PROPOSED — confirm at the Wednesday advisor meeting, then delete this parenthetical)

- Backend: Python 3.12, `meshtastic` PyPI library for radio I/O, FastAPI for the API, SQLite for
  dev with a schema that ports cleanly to PostgreSQL + PostGIS.
- Web: plain HTML/CSS/JS with Leaflet for maps; no framework until a concrete need is demonstrated.
- Tooling: `uv` for Python envs, `ruff` for lint+format, `pytest` for tests, `pre-commit` hooks.
- Record any change to the above as an ADR in `docs/adr/` before writing code against it.

## Commands

```
uv sync                      # install backend deps
uv run ruff check . && uv run ruff format --check .   # lint (CI runs this)
uv run pytest                # tests (CI runs this)
uv run backend/main.py       # run the ingest + API locally
```

Run lint and tests before every commit. If a command above is wrong or missing, fix it here.

## Git workflow (enforced by GitHub rulesets — do not try to work around them)

- `main` is protected. Nobody pushes to `main` directly, including admins.
- Every change goes on a branch named `<type>/<short-description>`, e.g. `feat/live-map-pings`,
  `fix/gps-timestamp-tz`, `docs/outreach-log`, `chore/ci-ruff`. Branch from an up-to-date `main`.
- Open a pull request early (draft is fine). A PR needs 2 approvals from the 3 teammates who did
  not author it, all CI checks green, and all review comments resolved before it can merge.
- Squash-merge only. The squash commit title becomes the changelog line, so make it read well.
- Commit messages follow Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`,
  `refactor:`. First line under 72 characters, imperative mood, body explains *why*.
- Never commit secrets, API keys, `.env` files, personal location data, or radio channel PSKs.
  Real channel keys live only on the devices and in a teammate's password manager.
- Never `git push --force` to a shared branch. Never rewrite history on `main`.
- Delete branches after merge.

## Coding conventions

- Small, focused PRs. One logical change per PR; split anything over ~400 changed lines.
- Every new module gets at least one test. Every bug fix gets a regression test.
- Type hints on all Python function signatures. Docstrings on public functions (one line is fine).
- Timestamps are stored in UTC as ISO-8601 and converted to local time only in the UI.
- Coordinates are WGS84 decimal degrees (lat, lon), stored as floats, never as strings.
- Log with the `logging` module, never `print`, in backend code.
- Prefer boring, well-documented libraries over clever ones. This has to be maintainable by a
  volunteer SAR team after we graduate.
- Match the existing style of the file you are editing. Do not reformat unrelated code in a PR.

## How Claude should behave in this repo

- Before writing code, read the relevant `docs/adr/` entries and the closest existing module.
- State assumptions explicitly. If a requirement is ambiguous, ask one focused question rather than
  guessing; if the teammate is unavailable, choose the simplest option and say so in the PR body.
- Do not invent SAR operational requirements. Anything about how real teams operate must trace to
  `docs/research/` or an outreach conversation logged in `docs/outreach/`.
- When asked to "review", check: correctness, tests, secrets, timestamp/coordinate handling, and
  whether the change matches an ADR. Report findings ranked by severity; do not pad with nits.
- Explain the reasoning behind recommendations, not just the conclusion. Pragmatic beats ideal.
- Never claim a test passed, a command ran, or a file exists without actually having done it.
- Keep responses tight. Code and diffs over prose. No emoji in code, commits, or docs.
- If you change a build/test command, a directory, or a convention, update this file in the same PR.

## Documentation conventions

- Meeting minutes: `docs/minutes/YYYY-MM-DD.md` (Diego owns these).
- Decisions: `docs/adr/NNNN-short-title.md` using the template in `docs/adr/0000-template.md`.
- Outreach: `docs/outreach/log.md` — one row per organization contacted: date, org, who, channel,
  status, notes. Never store a contact's personal phone/email in the repo; keep those in Discord DMs.
- README stays current. If the README describes something that no longer exists, fix the README.

## Safety and scope reminders

- This is a location-tracking system for people in the field. Treat position data as sensitive:
  minimize what is stored, make retention explicit, and never expose a public endpoint without auth.
- We are students building a prototype. The UI and docs must say so; nothing here is certified for
  life-safety use and the README carries that disclaimer.
