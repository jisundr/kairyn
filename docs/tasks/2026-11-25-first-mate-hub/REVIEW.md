---
task: 2026-11-25-first-mate-hub
stage: review
summary: "F3 and F2 are fixed (623 pass). 12 of 13 criteria have passing tests. AC13 stays a manual check after merge."
---

# Review: A first-mate hub that supervises AFK runs

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 Matched and unmatched PostToolUse commands | `test_post_tool_use_writes_label_and_exit_only_on_match` passes; T2 row. `bash_event` now starts from the real payloads in `tests/fixtures/hooks/`. `test_real_hook_payloads_give_label_and_exit` passes: `tests exit 0`, `tests exit 3`, `done` |
| AC2 Stop with a three-line message | `test_stop_writes_first_line_cut_to_200` passes; T2 row. The real `stop.json` has `last_assistant_message` |
| AC3 afk.py step writes the STATE.md text | `test_afk_update_mirrors_state_log_line` passes; T1 row |
| AC4 Tags with and without TMUX_PANE | `test_run_tag_from_tmux_pane_or_repo_folder` passes (tmux stub); T2 row |
| AC5 No log path, no file | `test_no_settings_writes_nothing`, `test_afk_writes_no_milestones_without_settings` pass; T1 row |
| AC6 `.session/` created and ignored by git | `test_session_folder_gets_gitignore` passes (checks `git status`); T1 row |
| AC7 Local watcher prints within 60 s and stores its number | `test_watch_local_prints_new_line_and_stores_number` passes; T1 row |
| AC8 SessionStart prints lines 3 to 5 and the instruction | `test_catchup_prints_missed_lines_and_instruction` passes; T3 row |
| AC9 ssh stub fails 3 times | `test_watch_host_unreachable_once_then_catches_up`, `test_retry_delays_double_from_15_seconds_to_5_minutes` pass; T4 row |
| AC10 Stored 10, log of 3 lines | `test_shorter_log_starts_from_line_one` passes (catchup and watch); T3 row |
| AC11 Default patterns | `test_default_patterns_match_common_commands` passes; T2 row |
| AC12 Each hook under 1 s on 10,000 lines | `test_hooks_finish_within_one_second` passes; T2 row |
| AC13 Real cerna-hq session, 0 "status?" asks | none: finding F1 |

`uv run pytest`: 623 passed in 85.16 s. The eval `milestones.yaml` has no run in this review.

Earlier findings:
- F3 (afk.py stops on a bad `milestones.yml`): fixed. `d4c5daf` puts `milestones.write` in `try` for `OSError` and `ValueError` and prints a `WARN`. `test_afk_run_goes_on_when_milestones_cannot_be_written` was red in `0347fc6` and passes now. It covers a bad line and a log path with no write access.
- F2 (made-up hook JSON): fixed. Three payloads from a `claude -p` run are in `tests/fixtures/hooks/`. They show that a success has no exit field and that a failure comes as `PostToolUseFailure` with `error: "Exit code N"`. `return_code` in `milestones.py` already reads both. The fixes did not change `milestones.py`.

## Gates
- accessibility: not set (REQUIREMENTS.md: not applicable).
- performance: not set. AC12 is the only evidence.
- observability: not set (REQUIREMENTS.md: not applicable).
- security: not set. A6 (no command text in the log) has evidence only in AC1: `s3cr3t` and `pytest` are not in the line.

## Risky files
- `plugin/hooks/hooks.json`: the hooks run on each Bash call, each failed Bash call and each turn end in every consumer repo. A slow or failing hook costs each user turn.
- `plugin/scripts/milestones.py`: `return_code` depends on the Claude Code payload shape. `fetch` builds an ssh shell command from the settings log path; `shlex.quote` protects it.
- `plugin/scripts/afk.py`: `update()` calls `milestones.write`. The `except` catches only `OSError` and `ValueError`. Another error type still stops the run.

## Findings
- F1: AC13 has no evidence. DESIGN.md makes it a manual check by Jayson after merge. The eval `milestones.yaml` checks only that the first mate starts Monitor and names missed lines, and it has no run in this task. R8 (a message per milestone in a real session) is not proven end to end.
- F2: Changes outside DESIGN.md: the `PostToolUseFailure` hook, `tests/test_afk.py`, `plugin/harness/.harness/README.md`, `plugin/release-hashes.json`, `.kairyn/learnings.md`, the backlog file and now `tests/fixtures/hooks/`. Review 1 in BUILD.md accepted the first four. They are needed, but DESIGN.md does not record them.
- F3: Open flag from BUILD.md: `tests/test_milestones.py` was edited in the fix round. The T1 to T5 red commits do not prove the tests that exist now.
- F4: `test_real_hook_payloads_give_label_and_exit` was never red. It passes on `milestones.py` from before the fixes. It is a guard on the payload shape, not proof of a code change. This is correct for F2, because the code was already right.
- F5: The fixtures come from one recorded run. The commit message tells how they were recorded, but no script records them again. If Claude Code changes the payload shape, no test or gate finds it.
- F6: The feat commit `d4c5daf` also changes `tests/fixtures/hooks/post_tool_use_failure.json` (only the `description` text). A green commit must not change test files. This change has no effect on the result.

Decision: pending
