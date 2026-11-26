---
task: 2026-11-26-effort-and-impact
stage: design
summary: "Option A: backlog_html.py reads effort and impact, sorts in Python, two filters; one hand pass sets TRIAGE.md, the README and 20 idea files."
---

# Design: effort and impact on backlog ideas, in place of appetite

## Approach
Option A. `backlog_html.py` swaps `appetite` for `effort` and `impact` in `FIELDS`. A new `level()` gives `low`, `medium`, `high` or `""` from the first word of a value, in any case (R9). `load_ideas` sorts the ideas: impact rank, then effort rank, then file name descending (R8, A4). The page script keeps `DATA` in that order. Two selects replace the appetite select (R7). Each row shows an Impact chip and an Effort chip; a dashed chip says Not set. The pane facts show the raw values (R6, R9). The header says "by impact, then effort". The docs and the 20 idea files change by hand from the approved `PROPOSALS.md` (R10).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Edit `backlog_html.py` in place, sort in Python, two fixed selects | One script, its tests, one fixture | Low: the page keeps its structure |
| B | A list of facets (field, values, order) that builds filters and sort | More code and tests | A layer for two fields |
| C | A as well as a sort select on the page | One more control and test | Not asked (A6) |

## Tasks
- T1: Effort and impact in the data, the row chips and the pane facts. `level()` for odd values. Remove `appetite_label`. Files: `plugin/scripts/backlog_html.py`, `tests/test_backlog_html.py`. Done: `uv run pytest tests/test_backlog_html.py` exits 0.
- T2: An effort filter and an impact filter, each Any, Low, Medium, High, Not set, with `aria-label`s, in place of the appetite filter. The empty-list text names filters, not appetite. Files: as T1. after: T1. Done: `uv run pytest tests/test_backlog_html.py` exits 0.
- T3: The sort order and the header text. Files: as T1. after: T1. Done: `uv run pytest tests/test_backlog_html.py` exits 0.
- T4: The backlog eval fixture gets `effort: low` and `impact: high`. Bump the version to 0.18.0 and run `uv run python scripts/release_hashes.py --write`. Files: `evals/promptfoo/provider.py`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`. after: T2, T3. Done: `uv run pytest` exits 0 and `grep -rni appetite plugin tests evals` prints nothing.
- T5: TRIAGE.md: agents capture, draft and propose effort and impact; a human triages, confirms them and commits. It names the log lines `[capture] ... Effort <e>, impact <i> proposed by the AI.` and `[triage] Effort <e>, impact <i> confirmed by <owner>.` Its Next notes use effort words, not big or small. README columns: Idea, Effort, Impact, Notes. Each of the 20 idea files: drop `appetite:`, add `effort:` and `impact:` from `PROPOSALS.md`, and a `[triage]` log line that names the owner. Not in a slice with a script: a one-off edit, checked by grep. Files: `docs/backlog/TRIAGE.md`, `docs/backlog/README.md`, `docs/backlog/2026*.md`. after: T4. Done: `uv run python plugin/scripts/budgets.py` exits 0 and `grep -l '^appetite:' docs/backlog/*.md` prints nothing.
- T6 (owner-requested change, 2026-11-26, PR #59): "Add color and sorting is missing." Chips get a colour by level, with the level word kept: green good (impact high, effort low), amber medium, grey impact low, red effort high, Not set neutral; light and dark tokens. A Sort select beside the filters: Best value (the default and the R8 order), Impact, Effort, Newest; the header names the active sort. Files: as T1. after: T5. Done: `uv run pytest tests/test_backlog_html.py` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 no `appetite:` field; each idea file has `effort:` and `impact:` | T5 | `grep -l '^appetite:'` empty; `grep -L '^effort:'` and `grep -L '^impact:'` on idea files empty |
| AC2 TRIAGE.md: AI proposes, owner confirms, no "appetite" | T5 | `grep -i appetite docs/backlog/TRIAGE.md` empty; read the rule |
| AC3 TRIAGE.md names the proposed and confirmed log lines | T5 | `grep 'proposed by the AI'` and `grep 'confirmed by'` in TRIAGE.md |
| AC4 README header `\| Idea \| Effort \| Impact \| Notes \|` | T5 | `grep -F` the header in README.md |
| AC5 effort and impact in row data and pane facts | T1 | pytest: `test_rows_and_pane_show_effort_and_impact` |
| AC6 two filters with five options each, no appetite filter | T2 | pytest: `test_page_has_effort_and_impact_filters` |
| AC7 R8 order with mixed and empty values and ties | T3 | pytest: `test_ideas_sort_by_impact_then_effort_then_newest` |
| AC8 `effort: Big (a note)` is Not set in the row, raw in the pane | T1 | pytest: `test_odd_value_counts_as_not_set` |
| AC9 idea values match `PROPOSALS.md`, with an owner log line | T5 | A one-off Python check that reads both and prints mismatches (none) |
| AC10 `grep -rni appetite plugin tests evals` prints nothing | T4 | That grep |
| T6 chip colours and the Sort control | T6 | pytest: `test_chips_are_coloured_by_level`, `test_level_colours_are_readable_in_both_themes`, `test_sort_control_changes_and_names_the_order` |

Eval plan (10 runs; costs from run 20261125T115929Z, PR #48, $0.05 per scenario):
- backlog: `# depends:` names `backlog_html.py`. 1 scenario, about $0.05.
- check: `plugin/scripts/*`. 1 scenario, about $0.05.
- init: `plugin/scripts/*`. 3 scenarios, about $0.15.
- upgrade: the bump rewrites `release-hashes.json`. 1 scenario, about $0.05.
Total about $0.30. The selector names the final list before the run.

Approval: Jayson De los Reyes, 2026-11-26T02:56:10Z, "approved DESIGN.md as written"
