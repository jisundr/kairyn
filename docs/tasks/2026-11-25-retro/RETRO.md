---
task: 2026-11-25-retro
stage: retro
summary: "12 entries: 2 move, 3 backlog, 7 drop. learnings.md goes from 567/1000 to the header and no entries."
---

# Retro: 2026-11-25

learnings.md before: 567/1000. After approval: about 10/1000 (header only).

| Entry | Action | Home or path | Text or reason |
|---|---|---|---|
| L1 | drop | `plugin/scripts/afk.py` | Stale: `parse_afk()` now reads the nested `repos:` map (task 2026-11-24-multi-repo, T1). |
| L2 | drop | `plugin/scripts/afk.py` | Stale: `targets()` gives each repo its own root, and each `gh` call runs there (T5). |
| L3 | backlog | `.harness/workflows/afk-run.md` | KAIRYN-OWNED. Text: "A child-repo task runs each done command in a checkout of the child repo. Write it with the child's test tool." |
| L4 | drop | `tests/test_afk_repos.py` | `test_t5_child_with_no_remote_blocks` holds the rule (review F1, fixed). |
| L5 | move | `.harness/workflows/testing-and-evals.md` | Merged with L12: "- An eval runs every scenario in its yaml file. Put a new scenario in its own file for the watch-it-fail run, then merge it. When you move or rename an eval test, run its new file once before a release." |
| L6 | drop | `tests/test_afk_repos.py` | `test_t5_retry_skips_a_merged_child` holds the rule (review F3, fixed). |
| L7 | drop | `scripts/release_hashes.py` | Stale: its docstring says every commit under a version counts, by design. |
| L8 | drop | `.harness/workflows/testing-and-evals.md` | L5 covers it after the move. |
| L9 | backlog | `plugin/scripts/afk.py` | Script: a retry of approve after a blocked merge needs a hand edit of `REVIEW.md` (review F5). |
| L10 | move | `.harness/workflows/change-a-stage.md` | "- A stage at its token budget takes a new rule only with cuts. Name each cut in the task's DESIGN.md, or the reviewer reads it as out of scope." |
| L11 | backlog | `plugin/scripts/afk.py` | Gate on agent-written code: flag a fix-round change to `plugin/stages/`, which no eval ran on. |
| L12 | drop | `.harness/workflows/testing-and-evals.md` | Merged into L5. |

Approval: Jayson De los Reyes, 2026-11-24T22:46:10Z, "approve the retro"
