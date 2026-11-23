---
name: gates
order: 4
purpose: Run the gates in .kairyn/afk.yml in order, security last; each exit code decides, then an AI check if set.
---

# Stage: gates

`afk.py` runs the gate commands. A model session runs only for a gate check, read-only, with the check in its prompt.

## Inputs
- `.kairyn/afk.yml`: the `gates:` list, one `<name>: <command>` line per gate, in order, security last.
- `checks:` in the same file: one `<name>: <check>` line for a gate that needs judgment, such as telemetry.

## Steps
1. Run each gate command from the repo root, in list order.
2. Exit 0 is `pass`. Any other exit is `fail`, and the run stops at that gate.
3. A gate with no command is `not set`. It is never a pass. `review` shows it to the human.
4. After a gate command passes, a gate with a check gets one session. In that session: read the diff, change nothing, and judge only the check. End with `PASS` or `FAIL: <one-line reason>`. A `FAIL` fails the gate.

## Output
`GATES.md` in the task folder: one row per gate with its result and exit code.

## Exit criteria
- [ ] Each gate is `pass` or `not set`, and each check printed `PASS`.

## State update
`afk.py` sets `gates: done` and `stage: review`. A failed gate sets `status: blocked` and logs the gate and its exit code.

## Learnings
None in this stage.
