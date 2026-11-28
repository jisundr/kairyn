---
name: grill
order: 40
optional: true
purpose: Interview the user in rounds of numbered questions until user and agent hold the same concept.
---

# Stage: grill

## Inputs
- A topic (new task) or a task folder (continue it).
- The task's `STATE.md` and `CONCEPT.md`, if present.
- The idea `STATE.md` names, if any: its raw request and problem.

## Steps
1. Get timestamps from `date` (`_template.md`, Time). For a topic, create the task folder and `STATE.md` as `requirements` step 1 does.
2. Read the repo first. Never ask what a file answers.
3. Ask for the problem before any solution. A named solution ("a cache") is a guess: ask if it fits the problem better than other fixes. Challenge each vague term: "faster" asks how fast, for whom.
4. Ask in rounds, then wait: `grill: in-progress`, `stage: grill`, `status: blocked`. A round asks the open questions whose prerequisites are settled: at most 3, those that unblock most first. Keep the rest under `## Open branches`. Numbers continue across rounds. End each message with, per question:
   `**Q<n>:** <one question>`
   `**Recommended:** <answer>, because <reason>.`
   Base each answer on the repo or earlier answers. Mark a guessed number `(guess)`.
5. Write each answer to `CONCEPT.md` as `D<n>`. A reply with no numbers accepts each recommendation. A question the reply skips stays open. Then ask the next round.
6. When no branch is open or the user says stop, restate the concept in at most 5 sentences and set `grill: done`. Ask the user to approve it. A stop is not approval.

## Output
`CONCEPT.md` in the task folder: fill `.kairyn/templates/CONCEPT.md`, in ASD-STE100 (`_template.md`, Writing). Keep its four `##` sections.

## Exit criteria
- [ ] The user approved the concept.

## State update
As in `_template.md`. Add `grill` to `stages`; log each answer. When you restate the concept: `grill: done`. Then follow `_approval.md`. Next stage: `stage: requirements`.

## Learnings
Append to `.kairyn/learnings.md`.
