---
name: design
order: 2
purpose: Choose an approach for approved requirements and plan its tasks and tests.
---

# Stage: design

## Inputs
- The task's `STATE.md` and `REQUIREMENTS.md`.
- `CONCEPT.md` and `.kairyn/learnings.md`, if present.

## Steps
1. Read `REQUIREMENTS.md`. If its `Approval:` line is missing or `pending`, write nothing. Ask for approval and stop.
2. Get timestamps from `date` (see `_template.md`, Time).
3. Read the code each acceptance criterion touches. Name only files you read. Mark new files `(new)`.
4. Take `CONCEPT.md` decisions as answers. Ask only what the repo leaves open.
5. Propose 2 or 3 options, each with cost and risk. One is the smallest thing that meets the requirements. Choose one.
6. Fill `.kairyn/templates/DESIGN.md`. Follow `_slices.md`.

## Output
`DESIGN.md` in the task folder, with only the template's sections, in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Each acceptance criterion has a task and a test.

## State update
Update `STATE.md` as in `_template.md`. Set `design` to `done`. All code in one `afk.yml` `repos:` entry: add `repo: <name>`. Then follow `_approval.md`. Keep `stage: design` until the user approves. Next stage: `stage: build`.
- The user names another option: rewrite `DESIGN.md` for it and keep `Approval: pending`.

## Learnings
Append repo learnings to `.kairyn/learnings.md`.
