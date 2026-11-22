---
name: requirements
order: 1
purpose: Turn a request into clear, scoped requirements with acceptance criteria.
---

# Stage: requirements

## Inputs
- A request (feature, bug or idea), or a task folder that `grill` started.
- `CONCEPT.md` and `.kairyn/learnings.md`, if present.

## Steps
1. Get timestamps from `date` (see `_template.md`, Time). Read each `docs/tasks/*/STATE.md`. If one has `requirements: pending` and matches the request, use its folder. Else create `docs/tasks/<YYYY-MM-DD>-<slug>/` and a `STATE.md` from `.kairyn/templates/STATE.md`.
2. Restate the request in one paragraph.
3. Skim the relevant code to ground the request.
4. Take the decisions and terms in `CONCEPT.md` as answers. List open questions; ask the user only those that neither the repo nor `CONCEPT.md` answers.
5. Do not add what the request does not ask for (docs, tests, output wording, design). Record a needed detail it does not give as an assumption: `A1`, `A2`.
6. Write the scope. Each "in" item comes from the request or an assumption. Put other ideas in "out".
7. Write acceptance criteria as a checklist a reviewer can verify. End each criterion with its source: `(request)`, an assumption `(A2)` or a decision `(D1)`.

## Output
Write `REQUIREMENTS.md` in the task folder from step 1:
- Front matter with `stage: requirements` (see `_template.md`, Output)
- Problem statement (only what the request says)
- Scope (in / out)
- Assumptions (`A1`, `A2`, ...)
- Acceptance criteria
- Open questions and the answers given

Write it in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Every acceptance criterion is verifiable and names its source.
- [ ] No unresolved open questions remain.

## State update
Update `STATE.md` as in `_template.md`. Set `requirements` to `done` in the front matter. Advance `stage`, or set `status: done` if no later stage exists. Log a one-line summary.

## Learnings
Append what this run taught about the repo to `.kairyn/learnings.md`.
