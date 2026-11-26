---
task: 2026-11-26-upgrade-help-runs-upgrade
stage: design
summary: "Option A: an argparse parser in each main() of upgrade.py and budgets_html.py, with the docstring as help text."
---

# Design: upgrade.py --help runs the upgrade

## Approach
Option A. Each `main()` builds its own `argparse.ArgumentParser` before it reads a file. argparse prints the usage and exits 0 on `-h`/`--help`. It exits 2 with the usage and the error on an unknown argument or a missing value. The parse comes before any file access, so these cases change no file (R1-R5). The defaults stay as they are now (R6, A1). The description is the module docstring with `RawDescriptionHelpFormatter`, as in `close.py` (A3).

`upgrade.py` keeps `main(argv)` and its two checks: `.kairyn/` must exist (exit 2), then `upgrade(root.resolve(), plugin.resolve())`. `budgets_html.py` stops calling `budgets.root_from_args`. `budgets.py` does not change (D1). The `/kairyn:upgrade` call `upgrade.py --root .` parses as before (K2).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | An argparse parser in each of the two `main()` functions. | About 10 lines per script, 6 new tests. | Low. argparse is in the standard library and Python 3.9. |
| B | A shared parse helper in `kairyn_files.py` for both scripts. | More lines. `budgets_html.py` then imports upgrade code. | Couples two unrelated scripts for 3 flags. |
| C | A hand check of `argv` against a list of known flags, like `backlog_html.py`. | About the same as A. | Against D3. Each script writes its own usage and error text. |

## Tasks
- T1: `upgrade.py` parses with argparse. Tests first in `tests/test_upgrade.py`: `--help` and `-h` exit 0, print the usage and leave the repo tree byte-equal. `--dry-run` and a bare `--root` exit 2, print the usage and an error to stderr and leave the tree byte-equal. Then change `main()`. Files: `tests/test_upgrade.py`, `plugin/scripts/upgrade.py`. Done: `uv run pytest tests/test_upgrade.py` exits 0.
- T2: `budgets_html.py` parses with argparse. Tests first in `tests/test_budgets_html.py`: `--help` and `-h` exit 0 and write no `budgets.html`. `--dry-run` and a bare `--out` exit 2 and write no `budgets.html`. Then change `main()`. Files: `tests/test_budgets_html.py`, `plugin/scripts/budgets_html.py`. after: T1. Done: `uv run pytest tests/test_budgets_html.py tests/test_python39.py` exits 0.
- T3: Release record. Bump `version` in `plugin/.claude-plugin/plugin.json` to the next free patch version (0.20.2 now; after PR #66, 0.21.1). Run `uv run python scripts/release_hashes.py --write`. `/kairyn:close` writes the `CHANGELOG.md` line. Files: `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`. after: T2. Done: `uv run pytest && claude plugin validate plugin` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 `upgrade.py --help`/`-h`: exit 0, usage, tree unchanged | T1 | `test_upgrade.py::test_help_prints_usage_and_changes_nothing` (parametrized `--help`, `-h`) |
| AC2 `budgets_html.py --help`/`-h`: exit 0, usage, no `budgets.html` | T2 | `test_budgets_html.py::test_help_prints_usage_and_writes_nothing` (parametrized `--help`, `-h`) |
| AC3 bad flag or bare flag: exit 2, usage and error on stderr, no change | T1, T2 | `test_upgrade.py::test_a_bad_argument_exits_2_and_changes_nothing` and `test_budgets_html.py::test_a_bad_argument_exits_2_and_writes_nothing` (parametrized `--dry-run`, bare flag) |
| AC4 both scripts build an `ArgumentParser` | T1, T2 | `test_upgrade.py::test_upgrade_parses_with_argparse` and `test_budgets_html.py::test_budgets_html_parses_with_argparse` read the source for `argparse.ArgumentParser(` |
| AC5 existing tests pass unchanged | T1, T2, T3 | `uv run pytest` with no edit to existing tests |
| AC6 `--root .` and `--root DIR --plugin DIR` act as before | T1 | the existing `test_upgrade.py` tests (they call `--root DIR --plugin DIR`), plus `test_root_dot_from_the_repo_upgrades` that runs `upgrade.py --root .` with `cwd` set to the repo |

Approval: Jayson De los Reyes, 2026-11-26T07:44:14Z, "Approve"
