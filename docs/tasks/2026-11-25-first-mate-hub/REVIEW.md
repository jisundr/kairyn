---
task: 2026-11-25-first-mate-hub
stage: review
summary: "12 of 13 criteria have passing tests (621 pass). AC13 is a manual check after merge. afk.py calls milestones.write with no guard."
---

# Review: A first-mate hub that supervises AFK runs

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 Matched and unmatched PostToolUse commands | `test_post_tool_use_writes_label_and_exit_only_on_match` passes; T2 row. The hook payload shapes are from the test, not from a real Claude Code event: finding F2 |
| AC2 Stop with a three-line message | `test_stop_writes_first_line_cut_to_200` passes; T2 row |
| AC3 afk.py step writes the STATE.md text | `test_afk_update_mirrors_state_log_line` passes; T1 row |
| AC4 Tags with and without TMUX_PANE | `test_run_tag_from_tmux_pane_or_repo_folder` passes (tmux stub); T2 row |
| AC5 No log path, no file | `test_no_settings_writes_nothing`, `test_afk_writes_no_milestones_without_settings` pass; T1 row |
| AC6 `.session/` created and ignored by git | `test_session_folder_gets_gitignore` passes (checks `git status`); T1 row |
| AC7 Local watcher prints within 60 s and stores its number | `test_watch_local_prints_new_line_and_stores_number` passes; T1 row |
| AC8 SessionStart prints lines 3 to 5 and the instruction | `test_catchup_prints_missed_lines_and_instruction` passes; T3 row |
| AC9 ssh stub fails 3 times | `test_watch_host_unreachable_once_then_catches_up` and `test_retry_delays_double_from_15_seconds_to_5_minutes` pass; T4 row |
| AC10 Stored 10, log of 3 lines | `test_shorter_log_starts_from_line_one` passes (catchup and watch); T3 row |
| AC11 Default patterns | `test_default_patterns_match_common_commands` passes; T2 row |
| AC12 Each hook under 1 s on 10,000 lines | `test_hooks_finish_within_one_second` passes; T2 row |
| AC13 Real cerna-hq session, 0 "status?" asks | none: finding F1 |

`uv run pytest`: 621 passed in 87.71 s. The eval `milestones.yaml` has no run in this review.

## Gates
- accessibility: not set (REQUIREMENTS.md: not applicable).
- performance: not set. AC12 is the only evidence.
- observability: not set (REQUIREMENTS.md: not applicable).
- security: not set. A6 (no command text in the log) has evidence only in AC1: `s3cr3t` and `pytest` are not in the line.

## Risky files
- `plugin/scripts/afk.py`: `update()` now calls `milestones.write`. An error there stops every AFK run in a repo with `.kairyn/milestones.yml`.
- `plugin/hooks/hooks.json`: the hooks run on each Bash call and each turn end in every consumer repo. A slow or failing hook costs each user turn.
- `plugin/scripts/milestones.py`: `fetch` builds a shell command for ssh from the settings log path. `shlex.quote` protects it now; a change there can run text from settings on the host.

## Findings
- F1: AC13 has no evidence. DESIGN.md makes it a manual check by Jayson after merge. The eval `milestones.yaml` checks only that the first mate starts Monitor and names missed lines. It has no run result in this task. R8 (a message per milestone in a real session) is not proven end to end.
- F2: The tests make the hook JSON themselves: `tool_response.exitCode` for PostToolUse and `error: "Exit code N"` for PostToolUseFailure. No test or eval reads a real Claude Code hook event. If the real Bash payload has no exit field and a failed command does not fire PostToolUseFailure, a failed test run is logged as `tests exit 0`.
- F3: `afk.py` `update()` calls `milestones.write` with no `try`. `parse_settings` raises `ValueError` on a bad line, and a log path with no write access raises `OSError`. Then `update()` fails after it wrote `STATE.md`, and the AFK run stops. The hooks catch all errors; afk.py does not. No test covers a bad `milestones.yml` for afk.py.
- F4: Changes outside DESIGN.md: the `PostToolUseFailure` hook in `plugin/hooks/hooks.json`, `tests/test_afk.py`, `plugin/harness/.harness/README.md`, `plugin/release-hashes.json`, `.kairyn/learnings.md` and the backlog file. Review 1 in BUILD.md accepted the first four. They are needed, but DESIGN.md does not record them.
- F5: Open flag from BUILD.md: `tests/test_milestones.py` was edited in the fix round. The red commits do not prove the tests that exist now.

Decision: Jayson De los Reyes, 2026-11-25T03:21:54Z, "fix F3 and F2"