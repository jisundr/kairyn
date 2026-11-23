---
name: review
order: 5
purpose: Check the built change against its requirements and hand the merge decision to the human.
---

# Stage: review

`afk.py` runs this stage in a fresh session with no user. The prompt names the task and the diff command.

## Inputs
- The task's `REQUIREMENTS.md`, `DESIGN.md`, `BUILD.md` and `GATES.md`.
- The diff of the change.

## Steps
1. Read the diff and each acceptance criterion in `REQUIREMENTS.md`.
2. For each criterion, name its evidence: a test that passes, a `BUILD.md` row or a gate. If you find none, it is a finding.
3. List each gate that is `not set` or failed, each flag and reviewer finding in `BUILD.md`, and each file where a defect costs most.
4. List findings: a criterion with no evidence, a change outside `DESIGN.md`, or a test that checks nothing.
5. Fill `.kairyn/templates/REVIEW.md`. Keep its last line `Decision: pending`.

Change no code and no other file.

## Output
`REVIEW.md` in the task folder, in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Each acceptance criterion has evidence or a finding.
- [ ] `REVIEW.md` ends with `Decision: pending`.

## State update
None. `afk.py` sets `status: blocked`. The human reads the diff and `REVIEW.md`, then runs `/kairyn:review <task> approve "<words>"` or `reject "<reason>"`.

## Learnings
Append one line to `.kairyn/learnings.md` for each finding and each flag left open, as a constraint: "Ban <X> with a lint rule or gate because <Y>".
