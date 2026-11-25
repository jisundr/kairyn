---
task: 2026-11-25-skill-names-clash
stage: review
summary: "All 11 criteria have test evidence. One finding: upgrade deletes an edited no-longer-shipped file when its .base/ copy is missing."
---

# Review: Skill names clash with built-in commands

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 `skills/close/SKILL.md` with `name: close`, no `skills/exit/` | `tests/test_skills.py`: `STAGE_SKILLS` has `close`; `test_no_exit_name_is_shipped[skills/exit]`. BUILD.md T2 (red 1, green 0). |
| AC2 `stages/CLOSE.md` with `name: close`, no `EXIT.md` | `tests/test_static.py` front-matter tests on `CLOSE.md`; `test_no_exit_name_is_shipped[stages/EXIT.md]`. BUILD.md T2. |
| AC3 `close.py` runs `check`, `adr-path`, `close`, `release`; no `exit.py` | `tests/test_close.py`, `tests/test_python39.py`; `test_no_exit_name_is_shipped[scripts/exit.py]`. BUILD.md T2. |
| AC4 `CLOSE.md` names `[close]` tags | `tests/test_static.py::test_close_stage_tags_its_lines_close`. BUILD.md T3. |
| AC5 no stage, skill or script name `exit` in shipped or tested files | `tests/test_static.py::test_no_shipped_or_tested_file_names_the_exit_stage` and `test_only_the_old_name_tests_mark_lines`. The AC5 grep shows only exit codes. BUILD.md T3. |
| AC6 unedited `EXIT.md` removed with `.base/` copy and entry | `tests/test_upgrade.py::test_an_unedited_file_no_longer_shipped_is_removed`. BUILD.md T1. |
| AC7 edited `EXIT.md` kept, `CONFLICT`, move-edits line, exit 1 | `tests/test_upgrade.py::test_an_edited_file_no_longer_shipped_is_kept_as_a_conflict_until_deleted`. BUILD.md T1. |
| AC8 delete it, upgrade again: `REMOVED`, new version | Same test, last part. BUILD.md T1. |
| AC9 recorded `EXIT.md` already missing: `REMOVED` | `tests/test_upgrade.py::test_a_recorded_file_already_deleted_is_removed_from_the_record`. BUILD.md T1. |
| AC10 unrecorded file at a no-longer-shipped path stays | `tests/test_upgrade.py::test_an_unrecorded_file_at_a_path_no_longer_shipped_stays`. BUILD.md T1. |
| AC11 `uv run pytest` and `claude plugin validate plugin` pass | Gate `testing` pass (exit 0). Re-run in review: 592 passed; `Validation passed`. |
| A5 this repo's `.kairyn/` upgraded | `tests/test_dev_harness.py::test_this_repo_kairyn_is_upgraded_to_the_plugin_version`. BUILD.md T4. |

## Gates
- accessibility: not set. REQUIREMENTS.md says not applicable.
- performance: not set. REQUIREMENTS.md says not applicable.
- observability: not set. The need (one `REMOVED` or `CONFLICT` line per file) has test evidence in AC6-AC9.
- security: not set. REQUIREMENTS.md says not applicable.

## Flags from BUILD.md
- Escape hatch: `# noqa` at `evals/promptfoo/asserts.py:14` and `evals/promptfoo/provider.py:17` in feat(T3).
- Test edits after the red commit: `tests/test_static.py` in feat(T4); `tests/test_dev_harness.py`, `tests/test_skills.py`, `tests/test_static.py`, `tests/test_upgrade.py` in fix commits. The fix commits answer review 1 and the decision to remove `test_plugin_version_is_0_11_0_or_later` (STATE.md, 2026-11-24T23:58:15Z).
- Reviewer findings: review 1 found files outside DESIGN.md. Commit d4561e9 added them to DESIGN.md. Review 2: none.

## Risky files
- `plugin/scripts/upgrade.py`: `_remove_unshipped` deletes files in consumer repos. A wrong unedited test deletes user edits, and git may not hold them.
- `tests/test_static.py`: the AC5 guard uses a wide allow-list regex (`CODE_USES`) and `# old-name` marks. A too-wide pattern lets a stage name `exit` pass.
- `.kairyn/manifest.json` and `.kairyn/.base/`: this repo's own record after the dogfood upgrade. A bad record breaks the next `/kairyn:upgrade` here.

## Findings
- F1: `upgrade.py` deletes an edited, no-longer-shipped file on the second run when its `.base/` copy is missing. `_remove_unshipped` stores the local bytes as the base (`Record(old.data if old else local, ...)`). The next run sees local equal to base and prints `REMOVED`. The user did not delete the file, so this breaks R7 and A2. Reproduction: `old_install`, edit `EXIT.md`, delete its `.base/` copy, upgrade twice. The output is `CONFLICT` then `REMOVED`, and the file is gone. Fix: for a pending no-longer-shipped entry, remove only when the local file is missing. Or record it with `no_base=True` and never auto-remove it. Add this case as a test.
- F2: K1 says the changed `close` eval and the `upgrade` eval run before merge. No `summary.md` from such a run is in the change, and `evals/results/` is not in this worktree. K3 also needs a new `close` pass record. Run `/run-evals close upgrade` before merge.

Decision: pending
