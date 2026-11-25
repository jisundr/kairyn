---
task: 2026-11-25-first-mate-hub
stage: requirements
summary: "Hooks and afk.py write tagged milestones to one log; a first-mate watcher sends each new line to the user, across restarts and ssh drops."
---

# Requirements: Milestone messages for the first mate

## Problem statement
The first mate wakes only when a whole server turn ends: 13 to 24 minutes. In one cerna-hq session the user asked "status?" 9 times, and restarts stopped 5 watchers. (D1, D2)

## Scope
In: a milestone log written by hooks and afk.py, a run tag per line, a watcher with restart and ssh catch-up, all in the kairyn plugin (D4 to D13)
Out: auto-resume, several crewmates, timed updates, a status view, a log copy (D3, D10, D14)

## Requirements
- R1: When a Bash command that matches a milestone pattern ends, the PostToolUse hook shall append its pattern label and exit code to the milestone log. (D6)
- R2: When a Claude turn ends, the Stop hook shall append the first line of the last assistant message to the milestone log. (D6)
- R3: When afk.py appends a log line to `STATE.md`, afk.py shall append the same text to the milestone log. (D4)
- R4: The writers shall write each line as `<UTC timestamp> [<run tag>] <text>`, with the text cut to 200 characters. (D11, A2)
- R5: The writers shall use `<tmux session>:<window> <repo folder>` as the run tag, the repo folder outside tmux, or the task slug for afk.py. (D11)
- R6: Where no milestone log path is set, the hooks and afk.py shall write nothing. (A1)
- R7: If the log folder `.session/` does not exist, the writer shall create it with a `.gitignore` that ignores all its files. (D7)
- R8: When a new line appears in the log, the watcher shall send it to the first mate within 60 seconds. (D3, A3)
- R9: The watcher shall store the number of the last line it sent in `.session/` of the first mate repo. (D10)
- R10: When a first mate session starts, the SessionStart hook shall print the lines after the stored number and tell the first mate to start the watcher. (D5)
- R11: If ssh to the host fails, the watcher shall send one "server unreachable since <time>" message and retry quietly with a growing delay of at most 5 minutes. (D12)
- R12: When ssh works again, the watcher shall send all lines after the stored number. (D12)
- R13: If the log has fewer lines than the stored number, the watcher shall send from line 1. (A4)
- R14: Where no host is set, the watcher shall read the log from the local disk. (D13)
- R15: The plugin shall read the patterns, log path and host from repo settings, with default patterns for tests, lint, `git push` and pull or merge request comments. (D6, D13)

## Non-functional needs
- Accessibility: not applicable: text in a log and in chat.
- Performance: each hook ends within 1 second. (A5)
- Security: log lines hold labels, not command text, so tokens stay out of the log. (A6)
- Observability: not applicable: this task is the observability feature.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Off until a log path is set; other repos see no change. | Jayson |
| A2 | assumption | 200 characters is enough for one milestone. (guess) | Jayson |
| A3 | assumption | 60 seconds is fast enough; the asks came 2 to 5 minutes apart. (guess) | Jayson |
| A4 | assumption | A shorter log means cleanup removed it. | design |
| A5 | assumption | 1 second per hook. (guess) | design |
| A6 | assumption | Command text can hold secrets. | Jayson |
| K1 | risk | A background command wakes Claude only when it exits, so the watcher exits per new line and is started again, or design finds a streaming tool. | design |
| K2 | risk | SessionStart can only print text; the model can skip starting the watcher. | design |
| K3 | risk | A child repo session has the home repo log path only through `--add-dir`. | design |
| K4 | risk | Hook text the model acts on needs evals, which cost tokens. | Jayson |
| D-1 | dependency | Plugin scripts run on Python 3.9 (`tests/test_python39.py`). | build |
| D-2 | dependency | The server gets the feature after a plugin update and `/kairyn:upgrade`. | Jayson |

## Acceptance criteria
- [ ] Tests feed PostToolUse a matched command with exit 1 and an unmatched command. Only the first adds a line, with label and `exit 1`, and no command text. (R1, R4)
- [ ] A test feeds Stop a three-line message. One line holds its first line, cut to 200 characters. (R2, R4)
- [ ] A test runs an afk.py step with a log path. The log gets the `STATE.md` text with the task slug tag. (R3, R5)
- [ ] Tests run a hook with and without `TMUX_PANE`. The tags match R5. (R5)
- [ ] A test with no log path writes no file. (R6)
- [ ] A test writes with no `.session/`. The folder and its `.gitignore` exist, and `git status` does not show it. (R7)
- [ ] A test appends to a local log. The watcher prints the line within 60 seconds and stores its number. (R8, R9, R14)
- [ ] A test starts SessionStart with stored number 2 and 5 lines. It prints lines 3 to 5 and the watcher instruction. (R10)
- [ ] A test gives the watcher an ssh stub that fails 3 times. It prints one message, waits at most 5 minutes per try, then the missed lines. (R11, R12)
- [ ] A test stores 10 with a 3-line log. The watcher prints from line 1. (R13)
- [ ] A test reads settings. Defaults match `uv run pytest`, `npm test`, `git push` and `gh pr comment`. (R15)
- [ ] A test times each hook on a 10,000-line log: under 1 second. (R1, R2)
- [ ] In one real cerna-hq session with tests, a push and a post, each milestone gives a message, and the user asks "status?" 0 times. (R1, R2, R8)

## Open questions and answers
- None. CONCEPT.md D1 to D14 answer the open points.

Approval: Jayson De los Reyes, 2026-11-25T01:34:11Z, "approved, run design"
