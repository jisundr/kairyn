---
task: 2026-11-26-effort-and-impact
stage: requirements
summary: "Effort and impact (low / medium / high) replace appetite in idea files, TRIAGE.md, the README table and the backlog page, which filters and sorts by them."
---

# Requirements: effort and impact on backlog ideas, in place of appetite

## Problem statement
A backlog idea has only `appetite` (big or small batch), set in 6 of 19 idea files. Nothing says what an idea is worth. The backlog page lists ideas newest first, so it cannot put high-impact, low-effort ideas first.

## Scope
In: `effort` and `impact` fields in idea files, TRIAGE.md rules, the README table, `plugin/scripts/backlog_html.py`, `tests/test_backlog_html.py`, the backlog eval fixture in `evals/promptfoo/provider.py`, values for each existing idea (D1-D6)
Out: other changes to the page; `RETRO.md` backlog entries (A5); old `[appetite]` log lines and `CHANGELOG.md` text, which are history

## Requirements
- R1: The idea file format shall have `effort:` and `impact:` front matter fields, each `low`, `medium`, `high` or empty, and no `appetite:` field. (D1, D2, A1)
- R2: TRIAGE.md shall say the AI proposes effort and impact at capture, and the owner confirms them at triage. It shall name no appetite. (D2, D3)
- R3: When an agent captures an idea, it shall write a proposed effort and impact and log them as proposed. (D3, A2)
- R4: When the owner triages an idea, the agent shall log the confirmed effort and impact with the owner's name. (D3, A2)
- R5: The backlog README table shall have the columns Idea, Effort, Impact and Notes, and no Appetite column. (D4, A3)
- R6: The backlog page shall show each idea's effort and impact in its list row and in its detail pane. (D4)
- R7: The backlog page shall have an effort filter and an impact filter, each with Any, Low, Medium, High and Not set. It shall have no appetite filter. (D6)
- R8: The backlog page shall list ideas by impact (high first), then effort (low first), then capture time (newest first). Ideas with no value sort after ideas with one. (D6, A4)
- R9: If a field value is not low, medium or high in any letter case, the backlog page shall count it as not set and show the raw value in the detail pane. (A1)
- R10: When the owner approves `PROPOSALS.md`, the agent shall write its effort and impact into each existing idea file and remove its `appetite:` line. (D5)

## Non-functional needs
- Accessibility: each filter has an `aria-label`, as the appetite filter has now. (A6)
- Performance: not applicable: the page holds about 20 ideas.
- Security: not applicable: the page stays offline and view only, with values escaped as now.
- Observability: not applicable: no runtime service.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Files and the README use lower case `low`, `medium`, `high`, like other field values. The page shows Low, Medium, High. | Jayson De los Reyes |
| A2 | assumption | No extra field marks "proposed". `status: inbox` and the log line say a value is not confirmed yet. | Jayson De los Reyes |
| A3 | assumption | The README keeps its rows (triaged ideas). Text after the appetite word moves to Notes. | Jayson De los Reyes |
| A4 | assumption | Ties sort newest capture first, the page's order today. | Jayson De los Reyes |
| A5 | assumption | `RETRO.md` step 6 stays as is: retro ideas get effort and impact at triage. It names no appetite, and a change re-runs the retro eval. | Jayson De los Reyes |
| A6 | assumption | The page's other parts, layout and phone width stay as they are. | Jayson De los Reyes |
| K1 | risk | Other repos that use `appetite:` lose it on the page. Their ideas show Not set until they add effort and impact. The changelog line says so. | Jayson De los Reyes |
| K2 | dependency | R2, R5 and R10 edit TRIAGE.md, the README and idea files. They wait until the open triage PR merges into main. | Orca coordinator |

## Acceptance criteria
- [ ] `grep -l '^appetite:' docs/backlog/*.md` prints nothing, and each idea file has `effort:` and `impact:`. (R1, R10)
- [ ] TRIAGE.md says the AI proposes effort and impact and the owner confirms them, and has no word "appetite". (R2)
- [ ] TRIAGE.md's capture and triage rules name the log lines for a proposed and a confirmed value. (R3, R4)
- [ ] The README table header is `| Idea | Effort | Impact | Notes |`. (R5)
- [ ] A test builds a page and finds effort and impact in each row's data and in the pane's facts. (R6)
- [ ] A test finds both filters with the options Any, Low, Medium, High, Not set, and no appetite filter. (R7)
- [ ] A test with ideas of mixed impact, effort, empty values and capture times gets the R8 order. (R8)
- [ ] A test with `effort: Big (a note)` shows Not set in the row and the raw value in the pane. (R9)
- [ ] Each idea file's values match the approved `PROPOSALS.md`, with a log line that names the owner. (R10)
- [ ] `grep -rni appetite plugin tests evals` prints nothing. (R1, R7)

## Open questions and answers
- Q1: How do ties sort? A: Newest capture first, as A4. The owner confirms. (coordinator, 2026-11-26)

Approval: pending
