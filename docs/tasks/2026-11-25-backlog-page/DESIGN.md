---
task: 2026-11-25-backlog-page
stage: design
summary: "Option A: one stdlib script plugin/scripts/backlog_html.py, a /kairyn:backlog command and a backlog eval, in 5 slices."
---

# Design: A visual index of the backlog

## Approach
Option A. One stdlib script parses the idea files, turns the markdown into HTML and fills one inline page template. A haiku command runs it, as `/kairyn:check` runs its checkers. Each rule that must always hold is in the script, so tests cover it with no model (R1-R17). The rendering code from WIP commit `c46a131` is rebuilt test-first, without status and without the font link (D5, D6, D8).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `plugin/scripts/backlog_html.py` (new): parse, markdown, page. `plugin/commands/backlog.md` (new) runs it. | 1 script, 1 command, 1 eval | One file holds parse, markdown and page: about 400 lines. |
| B | As A, with the markdown code in its own module `plugin/scripts/markdown_lite.py` (new) for later reuse. | 2 scripts | No second user of the module yet: more files for no need. |
| C | The command tells the model to write the HTML from the idea files. | No script | Output changes each run, and HTML escapes depend on the model. Breaks "script what must always work". |

## Tasks
- T1: Tracer bullet: the script writes `.kairyn/backlog.html` (new) with each idea title inline and prints its path; `/kairyn:backlog` runs it. Files: `plugin/scripts/backlog_html.py` (new), `plugin/commands/backlog.md` (new), `tests/test_backlog_html.py` (new), `tests/test_python39.py`. Done: `uv run pytest tests/test_backlog_html.py tests/test_python39.py` exits 0.
- T2: Each idea shows title, appetite, date and problem line, and opens to its text and log. The markdown renders with escapes, and idea-to-idea links go to `#<slug>`. Files: `plugin/scripts/backlog_html.py`, `tests/test_backlog_html.py`. after: T1. Done: `uv run pytest tests/test_backlog_html.py` exits 0.
- T3: Search, the appetite filter, the triage notes in `<details>`, system light and dark, phone width. No status and no network load. Files: `plugin/scripts/backlog_html.py`, `tests/test_backlog_html.py`. after: T2. Done: `uv run pytest tests/test_backlog_html.py` exits 0.
- T4: `.gitignore` gets one `.kairyn/backlog.html` line. A repo with no idea file or no `.kairyn/` gets one error line and exit 1. Files: `plugin/scripts/backlog_html.py`, `tests/test_backlog_html.py`. after: T1. Done: `uv run pytest tests/test_backlog_html.py` exits 0.
- T5: The `backlog` eval, the version bump and the README command list. Files: `evals/promptfoo/backlog.yaml` (new), `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `plugin/.claude-plugin/plugin.json`, `README.md`. after: T3, T4. Done: `uv run pytest` exits 0 and `claude plugin validate plugin` exits 0.

- T6: Readability, picked by the owner on 2026-11-25 from the UX research on PR #48. The phone overflow fix, with a test that measures width in Chrome. A compact list: the problem line is the first sentence, on one line. Aligned appetite and date columns: short appetite labels with a tooltip, `Nov 25` dates. A detail view that leads with the problem, with a log timeline. Search count, highlights, `/` to focus, and `No problem statement`. No date groups. Files: `plugin/scripts/backlog_html.py`, `tests/test_backlog_html.py`. after: T5. Done: `uv run pytest tests/test_backlog_html.py` exits 0.

Eval plan, 10 runs each. Costs are from the last run of each eval: run `20261123T211349Z`, its `summary.md` in the main checkout. `backlog` is new, so its cost is a guess from `check`.

| Eval | Why it runs | Scenarios | Cost at 10 runs |
|---|---|---|---|
| `backlog` (new) | new command and script | `backlog_page` | $0.05 (guess) |
| `check` | `# depends:` has `plugin/scripts/*` | `check_broken_doc` | $0.05 |
| `init` | `# depends:` has `plugin/scripts/*` | `init_fresh`, `init_keeps_edits`, `init_keeps_claude_md` | $0.15 ($0.05 each) |
| Total | | 5 | $0.25 (guess) |

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 `/kairyn:backlog` names the page, and it exists | T1, T5 | Eval `backlog`: `backlog_page` asserts the reply names `.kairyn/backlog.html` and the file exists. |
| AC2 one `<style>`, one `<script>` with no `src`, ideas inline | T1 | `test_page_is_one_inline_file` |
| AC3 no `<link`, `src=`, `@import`, `url(` or font URL | T3 | `test_page_loads_nothing_from_the_network` |
| AC4 one `.gitignore` line in each of 3 cases | T4 | `test_gitignore_gets_one_line` (parametrized: missing, without the line, with it) |
| AC5 title, appetite, date and problem line of 3 ideas | T2 | `test_lists_each_idea_with_its_fields` |
| AC6 no status word | T3 | `test_page_shows_no_status` |
| AC7 search, filter, open, Escape, link, themes, 360 px | T3, T6 | Manual: build this repo's page with `/kairyn:backlog`, open it in a browser, try each in light and dark at 360 px. |
| AC8 idea-to-idea link is `#<slug>` | T2 | `test_links_between_ideas_open_the_linked_idea` |
| AC9 Next and Parked in `<details>`, no other section | T3 | `test_triage_notes_keep_next_and_parked_only` |
| AC10 HTML escaped, `javascript:` dropped, `</script>` held | T2 | `test_idea_text_cannot_run_script` |
| AC11 no other `<input>`, `<select>` or `<button>` | T3 | `test_page_has_no_edit_controls` |
| AC12 no idea file or no `.kairyn/`: exit 1, one line, no write | T4 | `test_no_ideas_writes_nothing`, `test_no_kairyn_folder_writes_nothing` |
| AC13 runs on Python 3.9 | T1 | `test_backlog_script_runs` in `tests/test_python39.py` |
| AC14 tests, validate and version bump | T5 | `uv run pytest`, `claude plugin validate plugin`, `python3 scripts/check_version_bump.py origin/main` |

Approval: Jayson De los Reyes, 2026-11-25T11:48:00Z, "approved DESIGN.md as written"
