---
task: 2026-11-28-grill-rounds
stage: requirements
summary: "The grill stage asks up to 3 numbered questions per round, each with a recommended answer; the grill eval proves it."
---

# Requirements: Grill asks questions in numbered rounds

## Problem statement
`plugin/stages/GRILL.md` asks one question per message, so a long interview takes many turns. The user wants each message to ask the open questions whose prerequisites are settled, numbered, each with a recommended answer that "yes" accepts.

## Scope
In: the question step, `purpose` line and State update of `plugin/stages/GRILL.md` (request, D1)
In: the `description` of `plugin/skills/grill/SKILL.md` (A1)
In: the grill eval: a `rounds` metric in place of `one_question`, and `records_answers` per question (D6)
Out: an opt-in for one question per message (D7)
Out: a subagent for repo facts, and prototypes in place of questions (D2)
Out: a change to the `CONCEPT.md` template or its sections (D3)

## Requirements
- R1: When the grill stage asks the user, the grill stage shall ask between 1 and 3 numbered questions in one message, from the open questions whose prerequisites are settled. (D1)
- R2: If more than 3 questions are open with settled prerequisites, the grill stage shall ask the 3 that unblock the most and keep the others under `## Open branches` in `CONCEPT.md`. (D4)
- R3: The grill stage shall give each question in a round its own recommended answer with a reason. (request, D1)
- R4: The grill stage shall continue question numbers across rounds. (D8)
- R5: When a reply names no question numbers, the grill stage shall record each recommendation of the round as one `D<n>` decision in `CONCEPT.md`. (D5)
- R6: When a reply answers some question numbers of a round, the grill stage shall record those answers and keep the other questions open for the next round. (D5)
- R7: The grill eval shall fail a question turn with no numbered question, with more than 3, or with a question that has no recommended answer, and shall fail turn 0 with fewer than 2 questions. (D6)
- R8: The grill eval shall fail a run where an accepted round adds fewer `D<n>` decisions than it asked questions. (D6)
- R9: The grill eval shall keep the 4-reply scenario: two acceptances, a stop and an approval. (D6)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no source states one.
- Performance: not applicable: no source states one.
- Security: not applicable: no source states one.
- Observability: not applicable: no source states one.
- Size: `plugin/stages/GRILL.md` stays within its 500-token budget in `.harness/budgets.yml`. (CLAUDE.md)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | The skill `description` says "one question at a time" today, so it changes to rounds too. | design |
| A2 | assumption | This repo's `.kairyn/stages/GRILL.md` gets the new text through `upgrade.py` after the plugin version bump, not by hand. | design |
| K1 | risk | GRILL.md is at 448/500 tokens. The round rules need cuts elsewhere in the file. | design |
| K2 | risk | The fixture request opens fewer than 2 questions at turn 0, so R7 fails for a correct stage. | build (eval run) |
| K3 | risk | The new eval must fail on the current GRILL.md before the stage changes. | build (eval run) |

## Acceptance criteria
- [ ] `plugin/stages/GRILL.md` tells the stage to ask 1 to 3 numbered questions per round, from the settled frontier. (R1)
- [ ] `plugin/stages/GRILL.md` tells the stage to keep extra questions under Open branches and to ask the 3 that unblock the most. (R2)
- [ ] In the grill eval, each question turn has a Recommended line for each question. (R3)
- [ ] `plugin/stages/GRILL.md` tells the stage to continue numbers across rounds. (R4)
- [ ] In the grill eval, after each "I accept" reply, `CONCEPT.md` holds one more decision for each question of that round. (R5, R8)
- [ ] `plugin/stages/GRILL.md` tells the stage what to do with a reply that answers only some numbers. (R6)
- [ ] `uv run pytest` has tests for the round check: 0 questions, 1, 3, 4, a question with no recommendation, and turn 0 with 1 question. (R7)
- [ ] `evals/promptfoo/grill.yaml` lists `rounds` and not `one_question`, with the same 4 scripted replies. (R7, R9)
- [ ] The grill eval fails on the old GRILL.md and passes on the new one at 10 runs, with numbers from `summary.md`. (R1, R7, R8)
- [ ] `plugin/scripts/budgets.py` passes for `plugin/stages/GRILL.md`. (R1)

## Open questions and answers
- None: CONCEPT.md D1 to D8 answer each question.

Approval: Jayson De los Reyes, 2026-11-28T01:38:28Z, "Approve"
