---
task: 2026-11-26-effort-and-impact
stage: grill
summary: "Backlog ideas get effort and impact (Low / Medium / High) in place of appetite; the backlog page filters and sorts by them."
---

# Concept: effort and impact on backlog ideas, in place of appetite

## Concept
Each backlog idea gets two fields, effort and impact, each Low, Medium or High. Effort replaces appetite: no idea file, table or page keeps an appetite field. The AI proposes effort and impact when it captures an idea, and the owner confirms them at triage. Both show in the idea files, the backlog README table and the backlog page, which filters by both and lists ideas by impact (high first), then effort (low first). For the existing ideas, the AI proposes both in one list and the owner confirms the list.

## Decisions
- D1: Effort and impact both use the values Low, Medium and High. (user, 2026-11-26)
- D2: Effort replaces appetite. No appetite field remains. TRIAGE.md, the idea fields, `plugin/scripts/backlog_html.py`, its tests, docs and each stage or skill that names appetite change to match. (user, 2026-11-26)
- D3: The AI proposes effort and impact when it captures an idea. The owner confirms them at triage. (user, 2026-11-26)
- D4: Effort and impact show in the idea files, in the backlog README table (still a table, with one column for each) and on the backlog page. (user, 2026-11-26)
- D5: For each existing idea file, the AI proposes effort and impact. The owner confirms all of them in one list. (user, 2026-11-26)
- D6: The backlog page has a filter for effort and a filter for impact, in place of the appetite filter. It sorts ideas by impact (high first), then effort (low first). The requirements state how ties sort, as an assumption for the owner. (user, 2026-11-26)

## Terms
| Term | Meaning |
|---|---|
| effort | How much work an idea needs: Low, Medium or High. It replaces appetite. |
| impact | How much an idea is worth to kairyn users when it ships: Low, Medium or High. |
| proposed | A value the AI wrote that the owner did not confirm yet. |
| backlog page | `.kairyn/backlog.html`, written by `plugin/scripts/backlog_html.py` (`/kairyn:backlog`). |

## Open branches
- None. Source: the owner's grill on 2026-11-26, relayed by an Orca coordinator. Backlog idea `20261126024130-effort-and-impact`.

Approval: Jayson De los Reyes, 2026-11-26T02:41:30Z, "Grill answers: effort and impact are Low / Medium / High; effort replaces appetite; the AI proposes both at capture and the owner confirms at triage; both show in idea files, the README table and the backlog page; the AI proposes both for existing ideas in one list; the page filters by both and sorts by impact high first, then effort low first"
