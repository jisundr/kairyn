# 30. A backlog stage whose script does every write

Date: 2026-11-28

## Status
Accepted

## Context
Task 2026-11-28-backlog-stage. Ideas were captured, triaged, committed and pruned by hand from rules only this repo had (`docs/backlog/TRIAGE.md`). Plugin users got no backlog rules, and requirements did not start from a committed idea (D1).

## Decision
- kairyn ships an optional `backlog` stage, `BACKLOG.md`, that holds the idea rules (D3, D4).
- `/kairyn:idea <request>` captures one idea. `/kairyn:triage` lists inbox ideas and parked ideas past `review_by`, proposes keep, park or drop, and records each owner decision with the owner's name (D2, D3).
- `plugin/scripts/backlog.py` (`capture`, `digest`, `decide`, `commit`) does every file write. The model drafts and proposes; the owner decides (design option A).
- A commit sets `status: committed` and creates `docs/tasks/<date>-<idea slug>/STATE.md` that names the idea. Grill and requirements take that idea as the request (D5).
- No shape or pitch step: grill does the shaping. Init does not change: the first capture creates `docs/backlog/` (D2, D4).

## Consequences
- `TRIAGE.md` keeps only its Next and Parked notes.
- The task slug equals the idea slug, so close finds the idea (ADR 0026).
- In a real session, `/kairyn:triage` shows a permission prompt when it applies the owner's decisions: a skill's allowed tools cover only its own turn. The owner kept the prompt (PR #82); idea `triage-permission-prompt` is the follow-up.
