# pmp/data

Local only. Nothing in this folder is committed except this file and the `claude/` and
`archive/` placeholders.

- `terrain/<region>/`: terrain packages built by the select-a-region step (C-05), with their
  `manifest.json`.
- `missions/`: mission stores the daemon writes (C-01), one file per mission, named by mission
  id and start time (AAR Architecture v1.0 section 5.4). Where this folder finally lives, and how
  a copied mission finds its terrain package, is open (A-04).

No real person's position is stored anywhere until the retention rule (R-11) exists.
