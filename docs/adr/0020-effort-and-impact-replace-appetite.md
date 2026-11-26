# 20. Effort and impact replace appetite on backlog ideas

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-effort-and-impact. A backlog idea had only `appetite` (big or small batch), set in 6 of 19 idea files. Nothing said what an idea is worth, and the backlog page listed ideas newest first, so it could not put high-impact, low-effort ideas first.

## Decision
- Each idea has `effort` and `impact`, each `low`, `medium` or `high`. Effort replaces appetite: no idea file, table, page or stage keeps an appetite field (D1, D2).
- The AI proposes both at capture and logs them as proposed. The owner confirms both at triage, with a log line that names the owner (D3).
- The README table has the columns Idea, Effort, Impact and Notes (D4).
- The backlog page filters by effort and by impact. By default it lists ideas by impact (high first), then effort (low first), then newest capture (D6, A4). A Sort select and chip colours by level came from the owner's change T6.
- A value that is not low, medium or high counts as not set; the detail pane shows the raw value (R9).

## Consequences
- Old `[appetite]` log lines and CHANGELOG text stay as history.
- The 20 existing ideas got values from the approved `PROPOSALS.md` in one hand pass.
- A new idea has proposed values until triage; `status: inbox` and the log line mark them as not confirmed.
