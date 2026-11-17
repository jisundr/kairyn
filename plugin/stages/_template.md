---
name: <stage-name>
order: <number>
purpose: <one line: what this stage decides or produces>
---

# Stage: <stage-name>

## Inputs
- <what must exist before this stage starts, e.g. a prior stage's stone>

## Steps
1. <what the agent does>
2. <...>

## Output (the stone)
Write to `.kairyn/stones/<stage-name>/<YYYY-MM-DD>-<slug>.md`:
- <what the artifact must contain>

## Exit criteria
- [ ] <checkable condition that marks this stage done>

## Learnings
Append anything this run taught about the repo (conventions, pitfalls, commands)
to `.kairyn/learnings.md` so the next run starts smarter.
