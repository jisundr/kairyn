---
title: Milestones
summary: "How runs write milestone lines to one log, and how a first mate session streams them with Monitor. Setup in .kairyn/milestones.yml."
read_when: "setting up milestones.yml"
load: on-demand
---

# Milestones

A milestone is one log line: `<UTC time> [<run tag>] <text>`. Runs in the writer repo append lines. A first mate session in another repo (or the same repo) streams new lines as chat messages, so you do not have to ask for status.

No `.kairyn/milestones.yml`: milestones are off.

## Writer repo
```yaml
write:
  log: .session/milestones.log
  patterns:              # optional; replaces the defaults
    tests: '\bpytest\b'
```
- A Bash command that matches a pattern writes its label and exit code, never the command text. Defaults: tests, lint, push, comment.
- Each turn end writes the first line of the last message.
- `afk.py` writes each `STATE.md` log line, tagged with the task.
- The run tag is `<tmux session>:<window> <repo folder>`, or the repo folder outside tmux.
- `.session/` gets a `.gitignore`, so git ignores its files.

## First mate repo
```yaml
watch:
  host: dev-server                                # optional: read the log over ssh
  log: ~/Projects/home/.session/milestones.log
```
- At session start, a hook prints the lines since the last session. It tells Claude to start `milestones.py watch` with the Monitor tool.
- Each line that `watch` prints is one message. Monitor stops after 30 minutes. Start it again: `.session/watch.json` keeps the last line number, so no line is lost.
- With `host`, `watch` reads over `ssh`. If ssh fails, it prints `server unreachable since <time>` one time. It tries again after 15 seconds, then doubles the wait up to 5 minutes. Then it prints the missed lines.

## When messages stop
- Is Monitor running? Start the watcher again.
- Run `ssh <host> tail -3 <log>` to see if the log has new lines.
- A log that is shorter than the stored number starts again from line 1.
