---
task: 2026-11-26-upgrade-overwrites-running-stages
stage: design
summary: "upgrade() records a SAVED entry next to REPLACED; main() prints it with the next step. The repo doc goes back to the shipped copy."
---

# Design: Upgrade overwrites this repo's edited running-stages.md

## Approach
Option A. In `plugin/scripts/upgrade.py`, the branch that writes `<file>.kairyn-old` (line 141) also appends `("SAVED", <side file>)` to `lines`, after the `REPLACED` entry. The side file is `_file(repo, path)` made relative, so the block gives `CLAUDE.md.kairyn-old` (A3). `main()` prints a `SAVED` entry as `SAVED <file>.kairyn-old: your edited copy; kairyn owns <file> and replaced it. Move your edits into a file you own, then delete this one.` The exit code still comes only from `conflicts` (R4). The `/kairyn:upgrade` command text does not change (A1). Then `.harness/workflows/running-stages.md` goes back to the shipped copy (R5).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `upgrade()` adds a `SAVED` entry where it writes the `.kairyn-old`; `main()` prints it with the next step. | About 6 lines of code, 2 tests. | Other callers read `lines`. Only `main()` and `tests/test_upgrade.py` do, and they take any result word. |
| B | `main()` looks for `*.kairyn-old` files after the upgrade. | About 5 lines. | Also finds old `.kairyn-old` files from an earlier run, so R3 fails. |
| C | `upgrade()` returns a third value, the saved files. | About 8 lines, and each caller changes. | A new return shape for one line of output. |

## Tasks
- T1: Tracer bullet. Write two failing tests in `tests/test_upgrade.py`: an edited plugin-owned file gives a `SAVED <file>.kairyn-old` line with the next step and exit 0; an unedited one that the plugin changed gives `REPLACED` and no `SAVED` line. Then change `plugin/scripts/upgrade.py` (the `.kairyn-old` branch, `main()`, the docstring table). Files: `tests/test_upgrade.py`, `plugin/scripts/upgrade.py`. Done: `uv run pytest tests/test_upgrade.py` exits 0.
- T2: Docs and version. Remove the `union` note from `.harness/workflows/running-stages.md`. Add the `SAVED` line to the plugin-owned row of `.harness/workflows/upgrade.md`. Bump `plugin/.claude-plugin/plugin.json` to 0.20.1, run `uv run python scripts/release_hashes.py --write` and `uv run python plugin/scripts/harness_docs.py --write`. Files: `.harness/workflows/running-stages.md`, `.harness/workflows/upgrade.md`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`. after: T1. Done: `uv run pytest` exits 0.
- T3: Upgrade this repo to 0.20.1 with `python3 plugin/scripts/upgrade.py --root .`. Its output has no `SAVED` line, and `running-stages.md` does not change. Files: `.kairyn/manifest.json`. after: T2. Done: `uv run pytest && claude plugin validate plugin` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 an edited plugin-owned file gives `SAVED` with the next step, exit 0 | T1 | `test_edited_plugin_owned_file_prints_a_saved_line` (new) |
| AC2 an unedited replaced file gives no `SAVED` line | T1 | `test_an_unedited_replace_prints_no_saved_line` (new) |
| AC3 the repo doc is the shipped copy; `.gitattributes` keeps its comment | T2, T3 | `diff plugin/harness/.harness/workflows/running-stages.md .harness/workflows/running-stages.md` prints nothing; the T3 upgrade prints no `SAVED` line |
| AC4 `upgrade.md` names `SAVED`; the tests pass | T2 | `grep -n SAVED .harness/workflows/upgrade.md`; `uv run pytest` |

No evals: no instruction text changes (A1, approved).

Approval: Jayson De los Reyes, 2026-11-26T07:01:53Z, "Approve"
