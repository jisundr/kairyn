---
task: 2026-11-26-upgrade-help-runs-upgrade
stage: requirements
summary: "upgrade.py and budgets_html.py: --help prints usage and exits 0, a bad flag exits 2; neither changes a file."
---

# Requirements: upgrade.py --help runs the upgrade

## Problem statement
`plugin/scripts/upgrade.py` reads only `--root` and `--plugin` and ignores all other arguments. `upgrade.py --help` runs a real upgrade. On 2026-11-26 it replaced an edited `running-stages.md` in this repo. `budgets_html.py` also ignores `--help` and writes `.harness/budgets.html`. A flag with no value (`--root` at the end) stops both scripts with an `IndexError` trace.

## Scope
In: argument parsing in `plugin/scripts/upgrade.py` and `plugin/scripts/budgets_html.py`. (D1)
In: argparse for both scripts. (D3)
Out: `budgets.py`, `harness_docs.py`, `version_check.py`, `kairyn_files.py` and the other scripts. (D1)
Out: a `--dry-run` flag. (D4)
Out: changes to the upgrade rules or to the HTML page.

## Requirements
- R1: When the user gives `--help` or `-h`, `upgrade.py` shall print its usage and exit 0. (D2)
- R2: When the user gives `--help` or `-h`, `budgets_html.py` shall print its usage and exit 0. (D2)
- R3: If an argument is unknown, or a flag has no value, `upgrade.py` and `budgets_html.py` shall print the usage and the error and exit 2. (D2)
- R4: If `--help`, `-h`, an unknown argument or a flag with no value is given, `upgrade.py` and `budgets_html.py` shall change no file. (D2)
- R5: The scripts shall parse their arguments with argparse. (D3)
- R6: When the arguments are valid, `upgrade.py` and `budgets_html.py` shall behave as before, with the same output and exit codes. (A1)

## Non-functional needs
- Accessibility: not applicable: command-line scripts with no new output format.
- Performance: not applicable: no source states a need.
- Security: not applicable: no source states a need.
- Observability: not applicable: no source states a need.
- Compatibility: the scripts run on Python 3.9, as `tests/test_python39.py` checks. (A2)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | The defaults stay: `--root` is the current folder, `--plugin` is the script's plugin, `--out` is `.harness/budgets.html`. | design |
| A2 | assumption | The Python 3.9 rule in `test_python39.py` applies to the changed scripts. | design |
| A3 | assumption | The usage text comes from each script's docstring. | design |
| K1 | risk | The change touches `plugin/`, so CI `version-bump` needs a new version. PR #66 targets 0.21.0. If it lands first, this task takes the next free version. | build |
| K2 | risk | The `/kairyn:upgrade` command (`plugin/commands/upgrade.md`) calls `upgrade.py --root .`. A parse change that breaks this call breaks every upgrade. | build |

## Acceptance criteria
- [ ] A test runs `upgrade.py --help` and `-h` in an initialized repo: exit 0, usage on stdout, and every file is byte-equal to before. (R1, R4)
- [ ] A test runs `budgets_html.py --help` and `-h`: exit 0, usage on stdout, and no `budgets.html` exists after. (R2, R4)
- [ ] A test runs each script with `--dry-run` and with a bare `--root`: exit 2, usage and an error on stderr, and no file changes. (R3, R4)
- [ ] Both scripts import argparse and build an `ArgumentParser`. (R5)
- [ ] The existing tests in `tests/test_upgrade.py`, `tests/test_budgets_html.py` and `tests/test_python39.py` pass with no change to what they check. (R6)
- [ ] `upgrade.py --root .` and `upgrade.py --root DIR --plugin DIR` give the same results as before. (R6)

## Open questions and answers
- None.

Approval: Jayson De los Reyes, 2026-11-26T07:43:03Z, "Approve"
