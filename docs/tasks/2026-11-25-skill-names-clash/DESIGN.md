---
task: 2026-11-25-skill-names-clash
stage: design
summary: "Rename exit to close with git mv and text edits; add a removal step to upgrade.py for recorded files the plugin no longer ships."
---

# Design: Rename the exit stage to close

## Approach
Option A. It renames each shipped and tested file with `git mv` and edits each text that names the stage. In `upgrade.py`, a second pass after the shipped-file loop handles each manifest path that `installed_files()` no longer returns. It uses the same unedited test as the loop: the local copy matches `.base/` or a released hash. It meets R1-R10 with no new file format. It follows D4: the user moves edits by hand.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Rename by `git mv` and text edits. Add a removal pass in `upgrade.py` over recorded paths that are no longer shipped. | About 30 files, most with one-line edits. About 40 lines in `upgrade.py` plus 5 tests. | A missed text still says `exit`. A static test (T3) catches it. |
| B | Option A, plus a shipped `renames.json` (`EXIT.md` -> `CLOSE.md`). Upgrade merges an edited old file into the new file. | Option A plus a new file format, merge logic and tests. About 2 times the `upgrade.py` work. | Goes past D4 (the user moves edits). A wrong merge can move edits silently. |

## Tasks
- T1: Tracer bullet: the removal pass in `upgrade.py` for R6-R10, tested by an install from an old plugin copy that ships `stages/EXIT.md`, then an upgrade to a plugin that does not. The tests stay valid before and after T2. Files: `plugin/scripts/upgrade.py`, `tests/test_upgrade.py`, `.harness/workflows/upgrade.md`. Done: `uv run pytest tests/test_upgrade.py` exits 0.
- T2: Rename skill, stage and script: `git mv` of `plugin/skills/exit/` to `plugin/skills/close/`, `plugin/stages/EXIT.md` to `CLOSE.md` (`name: close`, `[close]` tags), `plugin/scripts/exit.py` to `close.py`. Update the callers and their tests. Files: `plugin/skills/close/SKILL.md`, `plugin/stages/CLOSE.md`, `plugin/scripts/close.py`, `plugin/commands/release.md`, `plugin/stages/RETRO.md`, `plugin/scripts/retro.py`, `tests/test_close.py` (renamed from `tests/test_exit.py`), `tests/test_skills.py`, `tests/test_python39.py`. after: T1. Done: `uv run pytest tests/test_close.py tests/test_skills.py tests/test_python39.py` exits 0.
- T3: Rename in docs and evals, and add a static guard. The guard fails when a shipped or tested file names the stage `exit`, the file `EXIT.md` or the script `exit.py`, or when `CLOSE.md` does not name `[close]`. Files: `tests/test_static.py`, `plugin/harness/.harness/workflows/task-lifecycle.md`, `plugin/harness/.harness/budgets.yml`, `.harness/workflows/task-lifecycle.md`, `README.md`, `evals/promptfoo/close.yaml` (renamed from `exit.yaml`), `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `evals/runner.py`, `evals/checks.py`, `tests/test_close_checks.py` (renamed from `tests/test_exit_checks.py`). after: T2. Done: `uv run pytest tests/test_static.py tests/test_close_checks.py` exits 0.
- T4: Release wiring and dogfood. Bump `plugin/.claude-plugin/plugin.json` to 0.11.0, run `uv run python scripts/release_hashes.py --write` and `uv run python plugin/scripts/harness_docs.py --write`. Run `upgrade.py` on this repo, so its `.kairyn/` drops `EXIT.md` and takes `CLOSE.md` (A5). Files: `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`, `.kairyn/stages/CLOSE.md` (new), `.kairyn/manifest.json`. after: T3. Done: `uv run pytest && claude plugin validate plugin` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 `skills/close/SKILL.md` exists, `skills/exit/` does not | T2 | `tests/test_skills.py`: `STAGE_SKILLS` maps `close` to `CLOSE`; a test asserts no `skills/exit/` |
| AC2 `stages/CLOSE.md` with `name: close`, no `EXIT.md` | T2 | `tests/test_static.py` front-matter test runs on `CLOSE.md`; `tests/test_skills.py` asserts no `stages/EXIT.md` |
| AC3 `close.py` runs its 4 subcommands, no `exit.py` | T2 | `tests/test_close.py` and `tests/test_python39.py` call `close.py`; a test asserts no `exit.py` |
| AC4 `CLOSE.md` names `[close]` tags | T3 | `tests/test_static.py`: `CLOSE.md` contains `[close]` and not `[exit]` |
| AC5 no stage, skill or script name `exit` in shipped or tested files | T3 | `tests/test_static.py`: grep guard over `plugin/`, `tests/`, `evals/promptfoo/`, `evals/*.py`, `README.md`; exit codes and `## Exit criteria` allowed |
| AC6 unedited `EXIT.md` removed with `.base/` copy and manifest entry | T1 | `tests/test_upgrade.py`: install from a plugin copy with `stages/EXIT.md`, upgrade to one without; expect `REMOVED` |
| AC7 edited `EXIT.md` kept, `CONFLICT`, move-edits line, exit code 1 | T1 | `tests/test_upgrade.py`: edit the file first; expect `CONFLICT` and return code 1 |
| AC8 delete it, upgrade again: `REMOVED`, manifest takes new version | T1 | `tests/test_upgrade.py`: continue the AC7 repo |
| AC9 recorded `EXIT.md` already missing: `REMOVED`, `.base/` copy gone | T1 | `tests/test_upgrade.py`: delete the file before upgrade |
| AC10 unrecorded file at a no-longer-shipped path stays | T1 | `tests/test_upgrade.py`: drop the manifest entry first; expect file untouched |
| AC11 `uv run pytest` and `claude plugin validate plugin` pass | T4 | T4 done command |

Approval: Jayson De los Reyes, 2026-11-24T23:20:37Z, "Yes, approved."
