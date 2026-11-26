---
task: 2026-11-26-upgrade-help-runs-upgrade
stage: grill
summary: "upgrade.py ignores unknown flags, so --help runs a real upgrade. Decide what the script does with --help and bad flags."
---

# Concept: upgrade.py --help runs the upgrade

## Concept
`upgrade.py` and `budgets_html.py` parse their arguments with argparse, like `close.py` and `afk.py`. `--help` or `-h` prints the usage and exits 0. An unknown flag, or a flag with no value, prints the usage and the error and exits 2. In both cases the script changes no file. The other scripts and a `--dry-run` flag are not in this task.

## Decisions
- D1: Fix `upgrade.py` and `budgets_html.py`. The read-only scripts stay as they are. (user: "upgrade.py and budgets_html.py")
- D2: `--help` exits 0. A bad flag exits 2. Neither changes a file. (user: "Yes: --help exits 0, a bad flag exits 2")
- D3: Parse with argparse, like `close.py` and `afk.py`. (user: "argparse, like close.py and afk.py")
- D4: No `--dry-run` flag in this task. (user: "No, not in this batch")

## Terms
| Term | Meaning |
|---|---|
| unknown flag | An argument that `main()` does not read, for example `--help` or `--dry-run`. |
| writing script | A script in `plugin/scripts/` that changes files when it runs. |

## Open branches
- None

Approval: Jayson De los Reyes, 2026-11-26T07:40:46Z, "Approve"
