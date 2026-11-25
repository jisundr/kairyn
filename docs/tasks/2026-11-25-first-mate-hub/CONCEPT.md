---
task: 2026-11-25-first-mate-hub
stage: grill
summary: "The first mate gets a message at each server milestone from one tagged log, so the user never asks for status."
---

# Concept: A first-mate hub that supervises AFK runs

## Concept
The first mate (cerna-hq) learns each milestone of server work as it happens, so the user never asks "status?". Hooks in the server Claude (PostToolUse on per-repo command patterns, Stop at turn end) and afk.py append tagged lines to one log, `cerna-home/.session/milestones.log`; the user also reads it in VS Code. A first-mate watcher reads the log over ssh, sends the user each new line, and stores only the last reported line number in `cerna-hq/.session/`. A SessionStart hook starts the watcher again and reports missed lines; on an ssh failure it tells the user once, retries quietly and catches up. It ships in the kairyn plugin with a host setting (no host: a local log); auto-resume and several crewmates are out of scope.

## Decisions
- D1: The problem is stale status. In cerna-hq, work runs in the server tmux session. The first mate does not see when it changes, so the user must ask for status. (user)
- D2: Evidence, cerna-hq session 2026-11-24 22:32 to 2026-11-25 01:03 UTC. The user asked "status?" 9 times. The first mate already starts a background watcher that wakes it when the server Claude goes idle. But it wakes only at the end of a whole server turn: 13 to 24 minutes for a full test run, a push and a post. Each "status?" came during such a wait. Two Orca restarts also stopped 5 watchers. (user asked to read the session; facts from its transcript and tmux pane)
- D3: During a long wait, the user gets a message at each milestone: tests done, pushed, posted, blocked. No timed updates, no status view. (user accepted)
- D4: Both AFK runs and free-form server Claude work send milestones. They write to one milestone log on disk: afk.py from its script, the server Claude during free-form work. One watcher wakes the first mate on each new line. (user accepted)
- D5: After a restart of the first mate session, the watcher starts again by itself (a SessionStart hook). It reports the log lines after the last one the first mate reported. (user accepted)
- D6: In free-form work, hooks in the server Claude write the milestones. PostToolUse writes a line when a command that matches a per-repo pattern list ends (tests, lint, push, MR post). Stop writes a line at each turn end, also when Claude asks the user. An instruction is only an optional extra. (user accepted)
- D7: Session files, the milestone log included, go in a git-ignored `.session/` folder in a repo the user sees in the ADE, not in `/tmp/hq-session/` and not in `.kairyn/`. Cleanup removes `.session/`. (user)
- D8: The setup has three tiers. cerna-hq is the first mate: local, the user talks to it. cerna-home is the home repo on the server (the home repo pattern): it holds the tasks. Child repos hold the code. (user)
- D9: The user also opens the server workspace (cerna-home and the child repos) in VS Code Remote, and watches tmux there. So the user sees server files and sees when the first mate report is older than the tmux pane. (user)
- D10: One milestone log: `cerna-home/.session/milestones.log` on the server. Hooks and afk.py write it. The user reads it in VS Code. The first mate watcher reads it over ssh and stores only the last line number it reported, in `cerna-hq/.session/`. No copy. (user)
- D11: Several runs share the one log. Each line has a run tag: the tmux window and the repo, or the task slug for an AFK run. Example: `2026-11-25T00:41Z [rivet:0 cerna-ui] tests passed (19,451)`. (user)
- D12: When ssh fails, the watcher tells the user once ("server unreachable since <time>"). Then it retries quietly with a growing delay, up to about 5 minutes (guess). When ssh works again, it reports the lines after the last reported line. (user)
- D13: It ships in the kairyn plugin: hooks, an afk.py writer and the watcher, in `plugin/scripts/`, with a host setting. With no host, the watcher reads a local `.session/` log, so local runs work too. (user accepted)
- D14: Scope is milestones only: hooks, the log and the watcher. Auto-resume after a block (afk-resume-blocked) and starting several crewmates (parallel-slices) stay separate backlog ideas. (user)

## Terms
| Term | Meaning |
|---|---|
| first mate | The local Claude session in cerna-hq. The user talks only to it. It drives the server session. |
| home repo | cerna-home on the server. It holds the tasks; child repos hold the code. |
| server session | The tmux session `rivet` on the dev server. The first mate sends keys to it and reads the pane back. |
| watcher | A background command in the first mate session that waits until the server Claude is idle, then wakes the first mate. |
| milestone log | `cerna-home/.session/milestones.log` on the server. Each line is one milestone: tests done, pushed, posted, blocked. |
| AFK run | One `/kairyn:build <task>` run of `afk.py`: build, gates, review. |

## Open branches
- None.
