---
name: grill
order: 40
optional: true
purpose: Interview the user one question at a time until user and agent hold the same concept.
---

# Stage: grill

Optional: run it before `requirements` on a vague or solution-first request. `/kairyn:grill` runs it.

## Inputs
- A topic (new task) or a task folder (continue it).
- The task's `STATE.md` and `CONCEPT.md`, if present.

## Steps
1. Get timestamps from `date` (see `_template.md`, Time). For a topic, create the task folder and `STATE.md` as `requirements` step 1 does.
2. Read the repo before each question. Never ask what a file answers.
3. Ask for the problem before any solution. A named solution ("a cache") is a guess: ask if it fits the problem better than other fixes. Challenge each vague term: "faster" asks how fast, for whom.
4. Ask one question per message, then wait: `grill: in-progress`, `stage: grill`, `status: blocked`. Follow each branch of the decision tree. End each message with:
   `**Q<n>:** <one question>`
   `**Recommended:** <answer>, because <reason>.`
   Give one answer, based on the repo or earlier answers. Mark a guessed number `(guess)`.
5. After each answer, write it to `CONCEPT.md` as `D<n>`. Then ask about a new open branch.
6. When no branch is open or the user says stop, restate the concept in at most 5 sentences and set `grill: done`. Ask the user to approve it. A stop is not approval.

## Output
`CONCEPT.md` in the task folder: fill `.kairyn/templates/CONCEPT.md`. Keep its four `##` sections.

Write it in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] The user approved the concept.

## State update
As in `_template.md`. Add `grill` to `stages`. Log each answer. When you restate the concept: `grill: done`. Then follow `_approval.md`. Next stage: `stage: requirements`.

## Learnings
Append to `.kairyn/learnings.md`.
