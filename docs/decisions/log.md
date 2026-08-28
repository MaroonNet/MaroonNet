# Decision log

Mirror of Project Bible Chapter 19, continued here so decisions made after v1.0 are in the repo.
Check this before reopening a settled question. One row per decision: date, decision, rationale.
Anything that changes the SOW schedule also gets an SOW version increment.

| Date | Decision | Rationale |
| ---- | -------- | --------- |
| 2026-08-27 | Repo hosted as a GitHub organization, public, GPL-3.0 | Org survives graduation; rulesets and secret scanning are free on public repos; Meshtastic firmware and Python library are GPL-3.0 |
| 2026-08-27 | `main` protected by ruleset: PR + 2 approvals, CI green, squash-only, signed commits, no bypass | Team decision at the first meeting; keeps every change reviewed by a majority of the non-authors |
| 2026-08-27 | Shared `CLAUDE.md` in the repo root governs Claude Code for all four members | One source of truth for AI-assisted output; edits go through PR |
| 2026-08-27 | Python deps managed with `uv` + `pyproject.toml` + committed `uv.lock` (exact pins) | Satisfies the Playbook "pin everything" rule with one tool; `uv export` produces `requirements.txt` for PyInstaller if needed |
| 2026-08-27 | Working title is MaroonNet; "Marooned" in Bible v1.0 is a stale first-pass name from an old source doc | Corey's correction; queue the fix for Bible v1.1 |
