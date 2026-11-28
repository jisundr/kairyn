---
task: 2026-11-28-grill-rounds
stage: grill
summary: "The grill stage asks each question with settled prerequisites in one numbered round, each with a recommended answer."
---

# Concept: Grill asks questions in numbered rounds

## Concept
The grill stage asks each round of questions in one message, not one question per message. A round holds the open questions whose prerequisites are settled, at most 3, the ones that unblock the most first. Each question has a number that continues across rounds and its own recommended answer. A reply with no numbers accepts each recommendation; a reply with some numbers leaves the others open for the next round. The grill eval proves it with a `rounds` metric in place of `one_question`, on the same 4-reply scenario.

## Decisions
- D1: Rounds are the default. One round has at most 3 questions. (user, backlog 2026-11-25)
- D2: No subagent for repo facts. No prototypes in place of questions. (user, backlog 2026-11-25)
- D3: Keep CONCEPT.md as the stage output. (user, backlog notes)
- D4: When the frontier holds more than 3 questions, the round asks the 3 that unblock the most. The others stay under Open branches. The next round recomputes the frontier. (user accepted)
- D5: A reply with no question numbers accepts each recommendation of the round. A reply that answers some numbers leaves the other questions open for the next round. (user accepted)
- D6: The eval replaces `one_question` with a `rounds` metric. Each question turn has 1 to 3 numbered questions, each with a Recommended line. Turn 0 has at least 2. `records_answers` checks one decision per accepted question. The 4-reply scenario stays. (user accepted)
- D7: No opt-in for one question per message. Rounds only. (user accepted)
- D8: Question numbers continue across rounds. Replies use those numbers. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| round | One grill message that asks numbered questions |
| frontier | The open questions whose prerequisites are settled |

## Open branches
None

Approval: Jayson De los Reyes, 2026-11-28T01:37:10Z, "Approve"
