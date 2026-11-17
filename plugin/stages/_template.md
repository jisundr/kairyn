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
When the stage finishes, update `STATE.md`: mark this stage done, set the
current stage to the next one, and record any open questions.

## Learnings
Append anything this run taught about the repo (conventions, pitfalls, commands)
to `.kairyn/learnings.md` so the next run starts smarter.
