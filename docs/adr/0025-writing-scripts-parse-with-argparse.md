# 25. Scripts that write files parse their arguments with argparse

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-upgrade-help-runs-upgrade. `upgrade.py` read only `--root` and `--plugin` and ignored all other arguments. `upgrade.py --help` ran a real upgrade and replaced an edited `running-stages.md` in this repo. `budgets_html.py` ignored `--help` too and wrote `.harness/budgets.html`. A flag with no value stopped both scripts with an `IndexError`.

## Decision
- `upgrade.py` and `budgets_html.py` parse their arguments with argparse, like `close.py` and `afk.py` (D1, D3).
- The parse comes before any file access. `--help` or `-h` prints the usage and exits 0. An unknown argument, or a flag with no value, prints the usage and the error and exits 2. Neither case changes a file (D2, R1-R4).
- The read-only scripts (`budgets.py`, `harness_docs.py`, `version_check.py`, `kairyn_files.py`) keep their hand parse (D1).
- No `--dry-run` flag (D4).

## Consequences
- A person who types `--help` or a wrong flag gets the usage, and no file changes.
- Valid arguments behave as before. `/kairyn:upgrade` still runs `upgrade.py --root .` (R6).
- A read-only script still ignores an unknown flag. It changes no file, so the cost is a run the user did not ask for.
