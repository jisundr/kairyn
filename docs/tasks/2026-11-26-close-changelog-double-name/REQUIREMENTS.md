---
task: 2026-11-26-close-changelog-double-name
stage: requirements
summary: "close.py writes the --entry as it is when it already contains the task name; else it adds ' (<task>)' as now."
---

# Requirements: close writes the task name once in the changelog line

## Problem statement
`close.py close` always writes `- <entry> (<task>)` to `CHANGELOG.md` (`cmd_close`). Recent entries end `(<task>; closes <idea>)`, and a model copies that form into `--entry`. Then the line names the task twice. Three lines in `CHANGELOG.md` show it, and the close of 2026-11-26-split-build-routing needed a fix by hand.

## Scope
In: the changelog line that `cmd_close` in `plugin/scripts/close.py` writes (D1, D2)
In: tests in `tests/test_close.py` for an entry with and without the task name (request)
In: a plugin version bump, because `plugin/` changes (A3)
Out: changes to `plugin/stages/CLOSE.md` or `.kairyn/stages/CLOSE.md` (D1)
Out: a fix of the three doubled lines already in `CHANGELOG.md` (A2)

## Requirements
- R1: If the `--entry` text contains the task name, then `close.py close` shall write `- <entry>` to `CHANGELOG.md` with no suffix. (D2)
- R2: If the `--entry` text does not contain the task name, then `close.py close` shall write `- <entry> (<task>)`, as it does now. (D2)
- R3: `close.py` shall find the task name as the exact, case-sensitive text of the `<task>` argument anywhere in the stripped entry. (A1)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a target.
- Security: not applicable: no new input or secret.
- Observability: not applicable: the `WROTE CHANGELOG.md` output does not change.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | "Contains the task name" means the full folder name, for example `2026-11-26-split-build-routing`. The slug alone (`split-build-routing`) does not count, so an entry that names only the slug still gets the suffix. | Jayson De los Reyes |
| A2 | assumption | The three doubled lines already in `CHANGELOG.md` stay. The fix applies to new entries only. | Jayson De los Reyes |
| A3 | assumption | The change to `plugin/scripts/close.py` needs a patch version bump and release hashes, as `scripts/check_version_bump.py` asks. | design |
| K1 | risk | An entry names the task for another reason, for example "follows 2026-11-26-x". Then close.py writes no suffix. The task name is in the line, so the line still names the task. | Jayson De los Reyes |
| K2 | risk | The `close` eval depends on `plugin/scripts/close.py` and re-runs. Its fixture entries have no task name, so its result does not change. | design |

## Acceptance criteria
- [ ] A test runs `close <task> --entry "Added X. (<task>; closes <idea>)"`. `CHANGELOG.md` gets `- Added X. (<task>; closes <idea>)`, and the task name is in it once. (R1, R3)
- [ ] A test runs `close <task> --entry "Added a dry run."`. `CHANGELOG.md` gets `- Added a dry run. (<task>)`. The existing close tests pass with no change. (R2)
- [ ] A test runs `close` with an entry that names only the slug, and one with the task name in other case. Each line gets ` (<task>)`. (R3)
- [ ] `uv run pytest`, `claude plugin validate plugin` and `python3 scripts/check_version_bump.py origin/main` exit 0. (R1-R3)

## Open questions and answers
- None. The owner confirms A1 and A2 with the approval.

Approval: pending
