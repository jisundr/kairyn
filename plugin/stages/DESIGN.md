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
1. Read `REQUIREMENTS.md`. If its `Approval:` line is missing or `pending`, write nothing. Tell the user to approve the requirements first, and stop.
2. Get timestamps from `date` (see `_template.md`, Time).
3. Read the code that each acceptance criterion touches. Name only files you read. Mark each file to create `(new)`.
4. Take `CONCEPT.md` decisions as answers. Ask only what the repo leaves open.
5. Propose 2 or 3 options, each with cost and risk. One is the smallest thing that meets the requirements. Choose one.
6. Fill `.kairyn/templates/DESIGN.md`. Split the chosen option into small tasks `T<n>` in dependency order, each with a done condition.
7. Number the acceptance criteria `AC<n>` in their `REQUIREMENTS.md` order. Give each one a Test plan row with its tasks and a test.

## Output
`DESIGN.md` in the task folder, with only the template's sections, in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Each acceptance criterion has a task and a test.
- [ ] Each named file exists or is marked `(new)`.

## State update
Update `STATE.md` as in `_template.md`. Set `design` to `done`, then:
- Until the user approves in chat: keep `Approval: pending`, set `status: blocked`, ask for approval. Never approve for the user.
- A reply that neither approves nor names an option changes nothing.
- The user names another option: rewrite `DESIGN.md` for it and keep `Approval: pending`.
- When the user approves: replace the line with `Approval: <git config user.name>, <timestamp>, "<the user's words>"`. Design is the last stage: set `status: done`.

## Learnings
Append what you learned about the repo to `.kairyn/learnings.md`.
