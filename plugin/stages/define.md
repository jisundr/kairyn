---
name: define
order: 1
purpose: Turn a request into a clear, scoped problem statement with acceptance criteria.
---

# Stage: define

## Inputs
- A feature request, bug report or idea (from the user's command arguments).
- `.kairyn/learnings.md`, if present.

## Steps
1. Restate the request in one paragraph.
2. Skim the relevant parts of the repo to ground the request in existing code.
3. List open questions; ask the user only those you cannot resolve from the repo.
4. Write the scope: what is in, what is explicitly out.
5. Write acceptance criteria as a checklist a reviewer could verify.

## Output (the stone)
Write to `.kairyn/stones/define/<YYYY-MM-DD>-<slug>.md`:
- Problem statement
- Scope (in / out)
- Acceptance criteria
- Open questions and the answers given

## Exit criteria
- [ ] Every acceptance criterion is verifiable.
- [ ] No unresolved open questions remain.

## Learnings
Append anything this run taught about the repo to `.kairyn/learnings.md`.
