---
title: Task lifecycle
summary: "Task folders, STATE.md fields and log format, and the clock rule for timestamps."
read_when: "starting or resuming a task, or touching STATE.md or task folders"
load: on-demand
---

# Task lifecycle

Each task has a folder: `docs/tasks/<YYYY-MM-DD>-<slug>/`, holding `STATE.md` and one upper-case file per stage (`REQUIREMENTS.md`). Stage outputs are files, not chat, so later stages and people can read them.

## STATE.md

Front matter is the source of truth. Read it, not the log, to see where a task is.

| Key | Meaning |
|---|---|
| `task`, `title` | Folder name and a human title |
| `stage` | Current stage |
| `status` | `in-progress`, `blocked` or `done` |
| `stages` | Each stage: `pending`, `in-progress` or `done` |
| `created`, `updated` | UTC timestamps |

The body is a `# Log`, newest last, one line per event: `<timestamp> [<stage>] <summary>`.

When a stage finishes: set it `done`, update `updated`, then
- another stage follows: set `stage` to it
- it was the last stage: leave `stage`, set `status: done`
- waiting on the user: set `status: blocked` and log why

## Time

Never write dates from memory. Use `date +%Y-%m-%d` for folder names and `date -u +%Y-%m-%dT%H:%M:%SZ` for timestamps.
