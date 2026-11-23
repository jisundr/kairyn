---
name: gates
order: 4
purpose: Run the gates in .kairyn/afk.yml in order; each exit code decides pass or fail.
---

# Stage: gates

`afk.py` runs this stage with no model session.

## Inputs
- `.kairyn/afk.yml`: the `gates:` list, one `<name>: <command>` line per gate, in order.

## Steps
1. Run each gate command from the repo root, in list order.
2. Exit 0 is `pass`. Any other exit is `fail`, and the run stops at that gate.
3. A gate with no command is `not set`. It is never a pass. `review` shows it to the human.

## Output
`GATES.md` in the task folder: one row per gate with its result and exit code.

## Exit criteria
- [ ] Each gate is `pass` or `not set`.

## State update
`afk.py` sets `gates: done` and `stage: review`. A failed gate sets `status: blocked` and logs the gate and its exit code.

## Learnings
None in this stage.
