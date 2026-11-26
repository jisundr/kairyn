---
task: 2026-11-26-effort-and-impact
stage: requirements
summary: "The AI's proposed effort and impact for each existing backlog idea (D5), for the owner to confirm in one list."
---

# Proposed effort and impact for existing ideas

One row per idea file in `docs/backlog/`, oldest first. Proposed by the AI; the owner confirms or changes each row (D5). Effort: the work, eval runs included. Impact: the value to kairyn users.

| Idea | Appetite now | Effort | Impact | Reason |
|---|---|---|---|---|
| backlog-stage | big batch | high | high | A new stage and command; every repo gets capture and triage. |
| release-stage | — | high | medium | A new optional stage; many repos have no monitoring config. |
| grill-rounds | big batch | high | high | Rewrite GRILL.md and its eval, no small slice; cuts turns in every grill. |
| approval-handoff | big batch | high | high | Shipped in #46; values for the record until release. |
| pir-stage | — | high | low | A new stage that needs release-stage first; incidents are rare. |
| hedge-words-in-backticks | — | low | low | One line in `_template.md`, run with the next change to it; avoids one false lint hit. |
| shared-harness-docs | — | low | low | One rule, but only this repo hits it and its homes are full. |
| parallel-slices | — | high | medium | Worktrees and merges in afk.py; faster AFK runs with independent slices. |
| grill-reads-private-notes | — | low | low | One line, but it helps only the author's own grills. |
| required-checks-app-id | — | low | low | One test; low risk with one maintainer. |
| ops-task-close | — | medium | medium | A close path for tasks with no requirements; overlaps backlog-stage. |
| several-child-repos | — | high | low | Multi-repo builds and a contract gate; no real task needs it yet. |
| split-design-stage | big batch | high | medium | The full split re-runs the design eval; it frees DESIGN.md's budget. |
| logs-as-bullet-lists | small batch | low | medium | A small diff, run with the next `_template.md` change; logs render in every PR. |
| rerecord-hook-fixtures | — | low | low | One script; nothing breaks until Claude Code changes the payloads. |
| grill-reads-other-repo-sessions | — | medium | low | A GRILL.md change with an eval first; reads private transcripts. |
| ship-review-gates | big batch | medium | high | Slices 1-2 shipped; only the `evals` gate is left; consumer repos get the gates. |
| upgrade-overwrites-running-stages | — | low | medium | Move one note; workers restored it by hand in 3 PRs. |
| close-fails-on-hand-merged-tasks | — | medium | high | A close.py command and tests; it broke the last 3 closes. |
| effort-and-impact (this task) | — | medium | medium | One script, its tests, one eval and 20 idea files; better triage order. |

Approval: pending
