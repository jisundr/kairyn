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
1. Read `REQUIREMENTS.md`. If its `Approval:` line is missing or `pending`, write nothing. Ask for requirements approval, and stop.
2. Get timestamps from `date`.
3. Read the code each acceptance criterion touches. Name only files you read.
4. Take `CONCEPT.md` decisions as answers. Ask only what the repo leaves open.
5. Propose 2 or 3 options, each with cost and risk. One is the smallest thing that meets the requirements. Choose one.
6. Fill `.kairyn/templates/DESIGN.md`. Cut the option into vertical slices `T<n>`, T1 the tracer bullet. Each slice crosses every layer, or says why not. Each has `after:` and `Done: `<command>``. Mark `(approval)` on a slice whose files match `.kairyn/afk.yml` `approval:`.
7. Number the acceptance criteria `AC<n>` in their `REQUIREMENTS.md` order. Give each one a Test plan row with its tasks and a test.

## Output
`DESIGN.md` in the task folder, with only the template's sections, in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Each acceptance criterion has a task and a test.
- [ ] Each named file exists or is marked `(new)`.

## State update
Update `STATE.md` as in `_template.md`. Set `design` to `done` (`repo: <name>` if one `repos:` repo has all code), then:
- Until the user approves in chat: keep `Approval: pending`, set `status: blocked`, ask for approval. Never approve for the user.
- A reply that neither approves nor names an option changes nothing.
- The user names another option: rewrite `DESIGN.md` for it and keep `Approval: pending`.
- When the user approves: replace the line with `Approval: <git config user.name>, <timestamp>, "<the user's words>"`. Set `stage: build`, `status: in-progress`.

## Learnings
Append repo learnings to `.kairyn/learnings.md`.
