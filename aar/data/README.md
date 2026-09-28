# data/

Everything here is local and is not committed (see `.gitignore`).

- `synthetic/`: mission stores written by `aar synth`. Safe to share; no real person is in them.
- `missions/`: mission stores from the simulator or from radios, once the daemon writes them.
  Position data of people in the field is sensitive. Nothing in this folder leaves this machine,
  and nothing from a real person is stored until the retention rule (R-11) exists.
