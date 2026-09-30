# data/

Everything here is rebuilt by the CLI and is not committed (see `.gitignore`).

- `cases/sources/<adapter>/`: raw files as downloaded, untouched
- `cases/cases.csv`: harmonized cases, one row per incident (written by `spm harmonize`)
- `cases/case_issues.csv`: every dropped or flagged case, with the reason
- `raw/`, `stacks/`: terrain downloads and derived feature stacks (build step 3)
