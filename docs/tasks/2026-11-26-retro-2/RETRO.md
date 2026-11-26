---
task: 2026-11-26-retro-2
stage: retro
summary: "Drop all 11 entries: 8 came back through the union merge of PR #66 after the approved retro 97e81eb; 3 are held elsewhere."
---

# Retro: 2026-11-26 (second)

learnings.md before: 579/1000. After approval: about 10/1000 (the header only).

L1 to L9 were removed by the approved retro of 2026-11-26 (commit 97e81eb). The merge of PR #66 added them again: `.gitattributes` merges `learnings.md` by `union`, and a union merge keeps lines that one side deleted.

| Entry | Action | Home or path | Text or reason |
|---|---|---|---|
| L1 | drop | `docs/backlog/20261126071901-phone-width-browser-test.md` | The backlog idea holds it (retro 97e81eb). |
| L2 | drop | `.harness/workflows/change-a-stage.md` | Line 31 holds the rule (retro 97e81eb). |
| L3 | drop | `docs/backlog/20261126071901-more-sessions-cost-more.md` | The backlog idea holds it (retro 97e81eb). |
| L4 | drop | `.kairyn/stages/CLOSE.md` | Stale: step 1 runs `record-merge`; L8 replaces it. |
| L5 | drop | `docs/backlog/20261126071901-headless-chrome-min-width.md` | The backlog idea holds it (retro 97e81eb). |
| L6 | drop | `plugin/scripts/backlog_html.py` | Stale: the backlog page has a Sort select. |
| L7 | drop | `docs/backlog/20261126071901-upgrade-help-runs-upgrade.md` | The backlog idea holds it (retro 97e81eb). |
| L8 | drop | `.harness/workflows/task-lifecycle.md` | "Close a task" names `record-merge`; CLOSE.md step 1 runs it. |
| L9 | drop | `.harness/workflows/upgrade.md` | Line 49 holds the rule (retro 97e81eb). |
| L10 | drop | `.harness/workflows/task-lifecycle.md` | "Where the template lives" names `evals/checks.py` as a part of the log format. |
| L11 | drop | `docs/backlog/20261126071901-upgrade-help-runs-upgrade.md` | Same as L7. |

New backlog idea (from this close, not an entry): `union-merge-restores-learnings`. A `union` merge of `learnings.md` restores lines that a retro removed on the other side, as PR #66 did. Home: `.gitattributes` or `retro.py`, so it goes to the backlog inbox.

Approval: pending
