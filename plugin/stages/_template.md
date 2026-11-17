---
name: <stage-name>
order: <number>
purpose: <one line: what this stage decides or produces>
---

# Stage: <stage-name>

Each task lives in its own folder: `docs/tasks/<YYYY-MM-DD>-<slug>/`.
`STATE.md` in that folder tracks which stage the task is in.

## Inputs
- `docs/tasks/<YYYY-MM-DD>-<slug>/STATE.md`
- <outputs of earlier stages this one needs, e.g. `REQUIREMENTS.md`>

## Steps
1. <what the agent does>
2. <...>

## Output
Write to `docs/tasks/<YYYY-MM-DD>-<slug>/<STAGE-NAME>.md` (stage name in caps):
- <what the file must contain>

## Exit criteria
- [ ] <checkable condition that marks this stage done>

## State update
`STATE.md` front matter is the source of truth for task state: read it, not the
log, to find the current stage. When the stage finishes:
- Front matter: set this stage to `done` in `stages`, update `updated`, and:
  - if another stage follows, set `stage` to it and keep `status: in-progress`;
  - if this was the last stage, leave `stage` as is and set `status: done`;
  - if waiting on the user, set `status: blocked` and log why.
- Log: append one line `<timestamp> [<stage-name>] <summary of what happened>`.

## Learnings
Append anything this run taught about the repo (conventions, pitfalls, commands)
to `.kairyn/learnings.md` so the next run starts smarter.
