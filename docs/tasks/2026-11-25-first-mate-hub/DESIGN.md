---
task: 2026-11-25-first-mate-hub
stage: design
summary: "One script, milestones.py: hooks and afk.py append tagged lines; the first mate streams new lines through Monitor and keeps its place in .session/."
---

# Design: Milestone messages for the first mate

## Approach
Option A. One script, `plugin/scripts/milestones.py`, has four commands: `hook` (PostToolUse and Stop), `write` (afk.py), `catchup` (SessionStart) and `watch`. The first mate runs `watch` with the Monitor tool: each stdout line is one chat message (R8). Monitor stops after 30 minutes; the first mate starts it again. The stored line number in `.session/watch.json` (new) makes a restart lose nothing (R9, R12).

Settings go in `.kairyn/milestones.yml` (new) (R15). It is optional: no file means off (R6, A1).
- Writer repo (cerna-home): `write: {log: .session/milestones.log, patterns: {<label>: <regex>}}`. The server Claude runs in the home repo, so `CLAUDE_PROJECT_DIR` finds the file (K3).
- First mate repo (cerna-hq): `watch: {host: rivet-os-dev-server, log: ~/Projects/cerna-home/.session/milestones.log}`. No `host`: a local file (R14).

afk.py writes its own lines from `update()`. It sets `KAIRYN_MILESTONES=off` for its `claude -p` sessions, so their hooks do not write from the worktree.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | One script; `watch` streams through Monitor; state in `.session/watch.json` (new) | 5 slices, about 400 lines | Monitor stops after 30 minutes; the first mate must start it again (K2). No line is lost. |
| B | Same script; `watch --once` in a background Bash that exits per batch | 5 slices | The first mate starts the watcher again after each milestone. One missed start means silence. |
| C | A tmux status bar and push notices, outside Claude | 3 slices | The first mate is not woken. It is a status view (out of scope, D3). |

## Tasks
- T1: Tracer bullet, local and AFK: `write` and `watch` with no host. `update()` in afk.py appends the same text with the task slug tag. `.session/` (new) gets a `.gitignore`. Files: `plugin/scripts/milestones.py` (new), `plugin/scripts/afk.py`, `tests/test_milestones.py` (new). Done: `uv run pytest tests/test_milestones.py tests/test_afk.py` exits 0.
- T2: Hooks: `hook` reads the hook JSON from stdin. PostToolUse writes the pattern label and exit code; Stop writes the first message line. Tag from `TMUX_PANE`, else the repo folder. Default patterns. afk.py sets `KAIRYN_MILESTONES=off`. Files: `plugin/scripts/milestones.py`, `plugin/hooks/hooks.json`, `plugin/scripts/afk.py`, `tests/test_milestones.py`. after: T1. Done: `uv run pytest tests/test_milestones.py tests/test_afk.py` exits 0.
- T3: Restart: `catchup` prints the lines after the stored number and the instruction to start `watch` with Monitor. A shorter log starts from line 1. Files: `plugin/scripts/milestones.py`, `plugin/hooks/hooks.json`, `tests/test_milestones.py`. after: T1. Done: `uv run pytest tests/test_milestones.py` exits 0.
- T4: Host: `watch` reads with `ssh <host> tail -n +<n>`. On failure it prints one "server unreachable since <time>" and stores it; it retries quietly from 15 seconds, doubling to 5 minutes. Files: `plugin/scripts/milestones.py`, `tests/test_milestones.py`. after: T1. Done: `uv run pytest tests/test_milestones.py` exits 0.
- T5: Docs and eval: a consumer doc `plugin/harness/.harness/workflows/milestones.md` (new) on setup, this repo's `.harness/workflows/milestones.md` (new), their budgets, and an eval that the first mate starts Monitor after the `catchup` text. Files: `.harness/budgets.yml`, `plugin/harness/.harness/budgets.yml`, `evals/promptfoo/milestones.yaml` (new), `evals/promptfoo/asserts.py`. after: T2, T3, T4. Done: `uv run pytest && uv run python plugin/scripts/harness_docs.py` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 Matched and unmatched PostToolUse commands | T2 | `test_post_tool_use_writes_label_and_exit_only_on_match` |
| AC2 Stop with a three-line message | T2 | `test_stop_writes_first_line_cut_to_200` |
| AC3 afk.py step writes the STATE.md text | T1 | `test_afk_update_mirrors_state_log_line` |
| AC4 Tags with and without TMUX_PANE | T2 | `test_run_tag_from_tmux_pane_or_repo_folder` |
| AC5 No log path, no file | T1 | `test_no_settings_writes_nothing` |
| AC6 `.session/` created and ignored by git | T1 | `test_session_folder_gets_gitignore` |
| AC7 Local watcher prints within 60 s and stores its number | T1 | `test_watch_local_prints_new_line_and_stores_number` |
| AC8 SessionStart prints lines 3 to 5 and the instruction | T3 | `test_catchup_prints_missed_lines_and_instruction` |
| AC9 ssh stub fails 3 times | T4 | `test_watch_host_unreachable_once_then_catches_up` |
| AC10 Stored 10, log of 3 lines | T3 | `test_shorter_log_starts_from_line_one` |
| AC11 Default patterns | T2 | `test_default_patterns_match_common_commands` |
| AC12 Each hook under 1 s on 10,000 lines | T2 | `test_hooks_finish_within_one_second` |
| AC13 Real cerna-hq session, 0 "status?" asks | T5 | Manual: Jayson runs one cerna-hq session after a plugin update, then counts the asks in its transcript. The eval `milestones.yaml` checks that the first mate starts Monitor. |

Approval: Jayson De los Reyes, 2026-11-25T01:36:34Z, "approved, run build"
