---
title: Task lifecycle
summary: "Task folders, STATE.md fields and log format, and the clock rule for timestamps."
read_when: "changing STATE.md, task folders or timestamps"
load: on-demand
---

# Task lifecycle

Each unit of work is a task with its own folder in the user's repo:

```
docs/tasks/<YYYY-MM-DD>-<slug>/
├── STATE.md            front matter = current state, body = log
├── REQUIREMENTS.md     output of the requirements stage (one file per stage, upper case)
└── DESIGN.md           output of the design stage
```

Stage outputs are files, not chat, so later stages (which run in a fresh context) can read them, a person can review them in git, and the repo keeps a history.

Each output starts with front matter: `task` (folder name), `stage` and a one-line `summary`. Identity only: task state stays in `STATE.md`, so the two cannot drift. `checks.output_header_problems` enforces it in the requirements eval.

## STATE.md

Front matter is the source of truth. Read it, not the log, to find where a task is.

| Key | Meaning |
|---|---|
| `task`, `title` | Folder name and a human title |
| `stage` | Current stage |
| `status` | `in-progress`, `blocked` or `done` |
| `stages` | Map of each stage to `pending`, `in-progress` or `done` |
| `created`, `updated` | UTC timestamps |

The body is a `# Log`, newest entry last, one line per event:

```
<timestamp> [<stage>] <summary of what happened>
```

When a stage finishes it sets its own stage to `done`, updates `updated`, then:
- another stage follows: set `stage` to it and keep `status: in-progress`
- it was the last stage: leave `stage` and set `status: done`
- waiting on the user: set `status: blocked` and log why

Open questions are not tracked in `STATE.md`. They live in `REQUIREMENTS.md`, and waiting on the user is expressed with `status: blocked`.

`requirements` always ends blocked: `REQUIREMENTS.md` ends with `Approval: pending` until the user approves in chat. The agent then writes `Approval: <git user.name>, <timestamp>, "<the user's words>"` and moves the task to `design`. `design` ends the same way with `DESIGN.md`; as the last stage, its approval sets `status: done`. `checks.approval_problems` enforces both forms.

## Time

The model cannot see the clock, and invented timestamps showed up as `T00:00:00Z`. Stages must get them from the system:

```bash
date +%Y-%m-%d                    # folder date
date -u +%Y-%m-%dT%H:%M:%SZ       # created, updated, log lines
```

The requirements eval rejects timestamps that are unparseable, look like placeholders (`T00:00:00Z`, `T12:00:00Z`) or fall outside the run's time window.

## Where the template lives

`plugin/templates/STATE.md` is copied to `.kairyn/templates/STATE.md` by init, and the requirements stage creates each task's `STATE.md` from it. Changing the format means updating the template, `_template.md`'s State update section, the stage files, `tests/test_static.py` and the eval checks in `evals/checks.py`.

## Close a task

After a task's change merges, `/kairyn:exit <task>` runs `EXIT.md`. It writes an ADR in `docs/adr/` for each load-bearing decision, a line under `## Unreleased` in `CHANGELOG.md` and learnings. Then `exit.py` deletes the task folder and its closed backlog files. Git history keeps them. If `learnings.md` is then past half its budget, `close` prints `RETRO:` and exit runs `RETRO.md`. `/kairyn:release <version>` moves `## Unreleased` to the version and tags it locally; you push the tag.
