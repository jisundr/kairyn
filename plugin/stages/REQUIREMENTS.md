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
5. Write the scope: what is in, what is explicitly out.
6. Write acceptance criteria as a checklist a reviewer could verify.

## Output
Write to `docs/tasks/<YYYY-MM-DD>-<slug>/REQUIREMENTS.md`:
- Front matter: `task`, `stage: requirements` and `summary` (see `_template.md`, Output)
- Problem statement
- Scope (in / out)
- Acceptance criteria
- Open questions and the answers given

Write it in ASD-STE100, about 80% of the way (see `_template.md`, Writing). The next stage reads it as its only input.

## Exit criteria
- [ ] Every acceptance criterion is verifiable.
- [ ] No unresolved open questions remain.

## State update
Update `STATE.md` as described in `_template.md`. Set `requirements` to `done` in the front matter. Advance `stage`, or set `status: done` if no later stage exists. Append a log line that summarizes the requirements.

## Learnings
Append anything this run taught about the repo to `.kairyn/learnings.md`.
