---
name: <stage-name>
order: <number>
purpose: <one line: what this stage decides or produces>
---

# Stage: <stage-name>

Each task has a folder `docs/tasks/<YYYY-MM-DD>-<slug>/`. Its `STATE.md` tracks the stage.

## Time
Never write dates or timestamps from memory. Use `date`:
- date for folder names: `date +%Y-%m-%d`
- timestamps (`created`, `updated`, log lines): `date -u +%Y-%m-%dT%H:%M:%SZ`

## Writing
Write every output file in ASD-STE100, about 80% of the way. A person or the next stage acts on it.
- Short sentences: at most 20 words for an instruction, 25 for a description.
- Active voice. No *should*, *would*, *may* or *might*, not even quoted from the request. Say what happens: "it would print" becomes "it prints".
- Keep real uncertainty as a condition: "If X, Y happens."
- Use the same term for the same thing every time.

## Inputs
- `docs/tasks/<YYYY-MM-DD>-<slug>/STATE.md`
- <outputs of earlier stages this one needs, e.g. `REQUIREMENTS.md`>

## Steps
1. <what the agent does>
2. <...>

## Output
Write to `docs/tasks/<YYYY-MM-DD>-<slug>/<STAGE-NAME>.md` (stage name in caps).
Start it with this front matter. Task state stays in `STATE.md`.
```yaml
---
task: <YYYY-MM-DD>-<slug>
stage: <stage-name>
summary: "<one line, at most 160 characters>"
---
```
Then:
- <what the file must contain>

## Exit criteria
- [ ] <checkable condition that marks this stage done>

## State update
`STATE.md` front matter is the task state, not the log. When the stage finishes:
- Front matter: set this stage to `done` in `stages`, update `updated`, and:
  - if another stage follows, set `stage` to it and keep `status: in-progress`;
  - if this was the last stage, leave `stage` and set `status: done`;
  - if waiting on the user, set `status: blocked` and log why.
- Log: append one line `<timestamp> [<stage-name>] <summary of what happened>`.

## Learnings
Append what this run taught about the repo to `.kairyn/learnings.md`.
