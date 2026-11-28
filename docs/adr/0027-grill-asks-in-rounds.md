# 27. Grill asks rounds of at most 3 numbered questions

Date: 2026-11-28

## Status
Accepted

## Context
Task 2026-11-28-grill-rounds. `plugin/stages/GRILL.md` asked one question per message, so a long interview took many turns. ADR 0002 describes that stage. Matt Pocock's `grilling` skill asks each question whose prerequisites are settled in one round. A "yes" to a full frontier hides decisions. `GRILL.md` was at 462/500 tokens.

## Decision
- A round asks the open questions whose prerequisites are settled: at most 3, the ones that unblock the most first. The rest stay under Open branches (D1, D4).
- Each question has its own recommended answer. Numbers continue across rounds (D8).
- A reply with no numbers accepts each recommendation. A reply with some numbers leaves the other questions open (D5).
- No opt-in for one question per message, no subagent for repo facts and no prototypes (D2, D7).
- The grill eval checks a `rounds` metric: 1 to 3 questions per turn, at least 2 at turn 0, one decision per accepted question (D6).

## Consequences
- An interview can cover every open branch before the eval's scripted stop. The eval accepts a concept restated after turn 0.
- `GRILL.md` is at 490/500 tokens. The "Optional: run it before `requirements`" line is gone; the skill description says when to run grill.
- A partial numbered reply has no eval scenario. Only the stage text covers it.
