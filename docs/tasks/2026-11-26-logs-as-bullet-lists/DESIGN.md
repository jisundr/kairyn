---
task: 2026-11-26-logs-as-bullet-lists
stage: design
summary: "Option A: change the log f-strings in afk.py and close.py and the bullet form in the templates and docs; version 0.21.0."
---

# Design: write STATE.md log entries as bullets

## Approach
Option A. Two script writers (`afk.py` `update()` line 368, `close.py` `record-merge` line 173) each append one f-string. Adding `- ` to each meets R1, R2 and R6: both append, and neither rewrites old lines. The stage rule, the template and the harness doc change in text only (R3, R4, R7). `upgrade.py` copies them to this repo's `.kairyn/` and `.harness/` (R5). `milestones.py` gets the text without the stamp, so it stays plain (R8).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Add `- ` to the two f-strings; edit the template, the rule and the doc. | About 10 changed lines plus 3 tests. | Low. The two scripts can drift apart later. |
| B | A, plus one shared `log_entry()` helper that both scripts import. | A new import between two scripts that share no module now. | Medium: a new coupling for a 2-character format. |
| C | A, plus a `/kairyn:check` rule that flags a plain entry added after a bullet entry. | A new check and its tests. | Medium: the requirements do not ask for it (D2 allows mixed logs). |

## Tasks
- T1: `afk.py` `update()` writes a bullet entry; a test runs `update()` on a `STATE.md` with a plain entry. Files: `plugin/scripts/afk.py`, `tests/test_afk_fixes.py`. Done: `uv run pytest tests/test_afk_fixes.py tests/test_afk.py -q` exits 0.
- T2: `close.py record-merge` writes a bullet entry; a test checks it and an old plain entry. Files: `plugin/scripts/close.py`, `tests/test_close_record_merge.py`. after: T1. Done: `uv run pytest tests/test_close_record_merge.py -q` exits 0.
- T3: The rule, the template and the doc show the bullet form; release 0.21.0; this repo takes it through `upgrade.py`. Files: `plugin/stages/_template.md`, `plugin/templates/STATE.md`, `plugin/harness/.harness/workflows/task-lifecycle.md`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`, `.kairyn/stages/_template.md`, `.kairyn/templates/STATE.md`, `.kairyn/.base/` copies, `.kairyn/manifest.json`, `.harness/workflows/task-lifecycle.md`, `CHANGELOG.md`. after: T2. Done: `uv run pytest -q && claude plugin validate plugin && uv run python plugin/scripts/budgets.py` exits 0.

T1 and T2 are each one layer (a script and its test): the scripts share no layer to cross. T3 has no script.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 `afk.py` writes a bullet entry | T1 | `tests/test_afk_fixes.py`: `Run.update()` adds `- <stamp> [build] <text>` as the last line. |
| AC2 `record-merge` writes a bullet entry | T2 | `tests/test_close_record_merge.py`: with a stub `gh`, the new line matches `^- \S+Z \[review\] Merged by hand`. |
| AC3 rule and template show bullets; `.kairyn/` copies match | T3 | `grep -n '^- <' plugin/templates/STATE.md`; `cmp` of each `.kairyn/` copy with its `plugin/` source. |
| AC4 old plain entries stay | T1, T2 | The tests of AC1 and AC2 start from a `STATE.md` with a plain entry and find it unchanged. |
| AC5 doc shows bullets; check passes | T3 | `/kairyn:check` (`harness_docs.py`, `budgets.py`) exits 0. |
| AC6 milestones unchanged | T3 | `git diff main --stat -- plugin/scripts/milestones.py tests/test_milestones.py` is empty. |
| AC7 pytest, validate, evals | T3 | `uv run pytest`, `claude plugin validate plugin`; then the selector-picked evals once, after the coordinator approves the list and cost (D3). |

Approval: Jayson De los Reyes, 2026-11-26T07:01:48Z, "Approve"
