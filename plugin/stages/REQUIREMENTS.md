---
name: requirements
order: 1
purpose: Turn a request into clear, scoped requirements with acceptance criteria.
---

# Stage: requirements

## Inputs
- A feature request, bug report or idea (from the user's command arguments).
- `.kairyn/learnings.md`, if present.

## Steps
1. Get the date and a UTC timestamp by running `date` (see `_template.md`, Time). Create the task folder `docs/tasks/<YYYY-MM-DD>-<slug>/` and a `STATE.md` from `.kairyn/templates/STATE.md`.
2. Restate the request in one paragraph.
3. Skim the relevant parts of the repo to ground the request in existing code.
4. List open questions; ask the user only those you cannot resolve from the repo.
5. Do not add what the request does not ask for (docs, tests, output wording, design). If a detail is necessary and the request does not give it, record it as a labeled assumption: `A1`, `A2`.
6. Write the scope. Each "in" item comes from the request or an assumption. Put other ideas in "out".
7. Write acceptance criteria as a checklist a reviewer could verify. End each criterion with its source: `(request)` or its labels, for example `(A2)`.

## Output
Write to `docs/tasks/<YYYY-MM-DD>-<slug>/REQUIREMENTS.md`:
- Problem statement (only what the request says)
- Scope (in / out)
- Assumptions (`A1`, `A2`, ...)
- Acceptance criteria
- Open questions and the answers given

Write it in ASD-STE100, about 80% of the way (see `_template.md`, Writing). The next stage reads it as its only input.

## Exit criteria
- [ ] Every acceptance criterion is verifiable and names its source.
- [ ] No unresolved open questions remain.

## State update
Update `STATE.md` as described in `_template.md`. Set `requirements` to `done` in the front matter. Advance `stage`, or set `status: done` if no later stage exists. Append a log line that summarizes the requirements.

## Learnings
Append anything this run taught about the repo to `.kairyn/learnings.md`.
