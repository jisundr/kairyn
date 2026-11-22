---
name: requirements
order: 1
purpose: Turn a request into approved, testable requirements with acceptance criteria.
---

# Stage: requirements

## Inputs
- A request, or a task folder from `grill`.
- `CONCEPT.md` and `.kairyn/learnings.md`, if present.

## Steps
1. Get timestamps from `date` (see `_template.md`, Time). Read each `docs/tasks/*/STATE.md`. If one has `requirements: pending` and matches the request, use its folder. Else create `docs/tasks/<YYYY-MM-DD>-<slug>/` and a `STATE.md` from `.kairyn/templates/STATE.md`.
2. Read the relevant code.
3. Take `CONCEPT.md` decisions as answers. Ask the user only what the repo and `CONCEPT.md` leave open.
4. Add nothing the request does not ask for. Record each needed detail it leaves out as an assumption `A<n>`.
5. Fill `.kairyn/templates/REQUIREMENTS.md`. Write each requirement as one EARS sentence that starts with The <system>, When, While, If or Where: "The CLI shall…", not "Each line shall…". End each "in" item, requirement and non-functional need with its source: `(request)`, `(A2)` or `(D1)`.
6. Give each assumption, risk (`K<n>`) and dependency the owner who confirms it.
7. Write acceptance criteria a reviewer can verify, each ending with the requirements it checks: `(R1)`. Each requirement needs one.

## Output
`REQUIREMENTS.md` in the task folder, in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Each requirement has a source and a criterion.
- [ ] No open questions remain.

## State update
Update `STATE.md` as in `_template.md`. Set `requirements` to `done`, then:
- Until the user approves in chat: keep `Approval: pending`, set `status: blocked`, ask for approval. Other replies are not approval. Never approve for the user.
- When the user approves: replace the line with `Approval: <git config user.name>, <timestamp>, "<the user's words>"`. Advance `stage`, or set `status: done` if no stage follows.

## Learnings
Append what you learned about the repo to `.kairyn/learnings.md`.
