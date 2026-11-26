---
task: 2026-11-26-close-changelog-double-name
stage: design
summary: "cmd_close adds ' (<task>)' only when the entry lacks the task name; two CHANGELOG lines lose their second task; patch bump 0.17.1."
---

# Design: close writes the task name once in the changelog line

## Approach
Option A. In `cmd_close` in `plugin/scripts/close.py`, the line is `- <entry>` if the stripped entry contains `task`, else `- <entry> (<task>)` (R1, R2). The check is a plain `task in entry`: exact, case-sensitive, full folder name (R3, A1). Two `CHANGELOG.md` lines lose their second ` (<task>)` by hand, and a test keeps every line to one task name (R4, A2). `plugin/stages/CLOSE.md` does not change (D1).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | One condition in `cmd_close`; fix two `CHANGELOG.md` lines by hand; a test scans `CHANGELOG.md`. | About 5 lines of code, 4 tests. | K1: an entry that names the task for another reason gets no suffix. The task name is still in the line. |
| B | As A, and `add_entry` also removes a second task name from any line it writes. | More code in `add_entry`, and more cases to test. | It edits text the model wrote. The requirements do not ask for it. |
| C | Tell the model in `CLOSE.md` to leave the task out of `--entry`. | One sentence, and an eval run. | D1 excludes it. A model can still ignore it. |

## Tasks
- T1: Tracer bullet: `close <task> --entry` with the task name writes the entry with no suffix; without it, as now. Tests first in `tests/test_close.py`: entry with `(<task>; closes <idea>)`, plain entry, slug-only entry, task name in other case. Files: `plugin/scripts/close.py`, `tests/test_close.py`. Done: `uv run pytest tests/test_close.py` exits 0.
- T2: `CHANGELOG.md` names each task once. Test first: `test_changelog_names_each_task_once` in `tests/test_close.py` reads the repo `CHANGELOG.md` and fails on a line where a `YYYY-MM-DD-<slug>` name occurs twice. Then fix the lines of 2026-11-24-public-ready and 2026-11-24-retro. Files: `CHANGELOG.md`, `tests/test_close.py`. after: T1. Done: `uv run pytest tests/test_close.py` exits 0.
- T3: Release: bump `plugin/.claude-plugin/plugin.json` to 0.17.1 (A3), run `python3 scripts/release_hashes.py --write`, and run `/kairyn:upgrade` for this repo's `.kairyn/`. close.py is not an installed file, so only the manifest version changes. Files: `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`, `.kairyn/manifest.json`. after: T1. Done: `python3 scripts/check_version_bump.py origin/main`, `claude plugin validate plugin` and `uv run pytest` exit 0.

Eval plan, 10 runs each, as the selector picks them (`# depends:`). Costs: the last 10-run `summary.md` on disk with these evals (main checkout, run 20261123T211349Z; close was named exit then). The 2026-11-25 summaries are not on this machine.

| Eval | Why it runs | Scenarios | Last cost at 10 runs |
|---|---|---|---|
| `close` | `plugin/scripts/close.py` | `close_decision`, `close_plain`, `close_retro` | $4.73 ($1.38, $1.19, $2.16; Sonnet) |
| `check` | `plugin/scripts/*` | `check_broken_doc` | $0.05 |
| `init` | `plugin/scripts/*` | `init_fresh`, `init_keeps_edits`, `init_keeps_claude_md` | $0.15 |
| `upgrade` | `plugin/release-hashes.json` | `upgrade_conflict` | $0.05 |
| Total | | 8 | $4.98 |

K2: the `close` fixture entries hold no task name, so the result does not change. `check`, `init` and `upgrade` run scripts only, at about $0.05 per scenario.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 entry with the task name gets no suffix; the name occurs once | T1 | `test_close_keeps_an_entry_that_names_the_task` |
| AC2 plain entry gets ` (<task>)`; existing close tests pass unchanged | T1 | `test_close_adds_the_task_to_a_plain_entry`, existing `tests/test_close.py` |
| AC3 slug-only entry and other-case entry each get ` (<task>)` | T1 | `test_close_adds_the_task_when_only_the_slug_or_other_case_names_it` |
| AC4 no `CHANGELOG.md` line names a task twice; fails on main | T2 | `test_changelog_names_each_task_once` |
| AC5 pytest, plugin validate and version-bump check exit 0 | T3 | `uv run pytest`; `claude plugin validate plugin`; `python3 scripts/check_version_bump.py origin/main`; eval `close` (plan above) |

Approval: pending
