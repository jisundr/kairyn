---
title: Task lifecycle
summary: "Task folders, STATE.md fields and log format, and the clock rule for timestamps."
read_when: "starting or resuming a task, or touching STATE.md or task folders"
load: on-demand
---

# Task lifecycle

Each task has a folder: `docs/tasks/<YYYY-MM-DD>-<slug>/`, holding `STATE.md` and one upper-case file per stage (`REQUIREMENTS.md`). Stage outputs are files, not chat, so later stages and people can read them.

Each stage output starts with front matter that names it: `task`, `stage` and a one-line `summary`. It holds no task state. `head -5` tells you what a file is.

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
- waiting on the user: set `status: blocked` and log why (`requirements` and `design` wait here until the user approves their output)

Each task runs `requirements`, `design`, `build`, `gates`, `review`. `afk.py` updates `STATE.md` for the last three. The merge decision in `REVIEW.md` sets `status: done`.

## Time

Never write dates from memory. Use `date +%Y-%m-%d` for folder names and `date -u +%Y-%m-%dT%H:%M:%SZ` for timestamps.

## Close a task

After a task's change merges, `/kairyn:close <task>` runs `CLOSE.md`. A task merged by hand, not by `/kairyn:review approve`, is not done yet: `close.py record-merge` reads the merged pull request through `gh` (`--pr <n>`, else the last `PR #<n>` in `STATE.md`, else its branch) and writes `status: done` and a `REVIEW.md` `Decision:` line from it. It writes an ADR in `docs/adr/` for each load-bearing decision, a line under `## Unreleased` in `CHANGELOG.md` and learnings. Then `close.py` deletes the task folder and its closed backlog files. Git history keeps them. With no git, `close.py` first copies them to `.kairyn/archive/`. If `learnings.md` is then past half its budget, `close` prints `RETRO:` and the stage runs `RETRO.md`. `/kairyn:release <version>` moves `## Unreleased` to the version and tags it locally; you push the tag.
