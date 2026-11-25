---
task: 2026-11-25-backlog-page
stage: requirements
summary: "/kairyn:backlog writes .kairyn/backlog.html: an offline, view-only index of every idea file, with search, appetite filter and detail view."
---

# Requirements: A visual index of the backlog

## Problem statement
`docs/backlog/README.md` lists triaged ideas only. No single view shows every idea with its appetite, date and problem, in this repo or a consumer repo.

## Scope
In: `/kairyn:backlog` and a stdlib script in `plugin/scripts/` that writes `.kairyn/backlog.html`. (D1, D7)
In: a version bump, Python 3.9 support, tests and an eval. (D1)
Out: edits from the page, and status on the page. (D3, D6)
Out: a committed page, or a page that other stages rebuild. (D4)
Out: the repo-only `scripts/backlog_html.py`. (D8)

## Requirements
- R1: When the user runs `/kairyn:backlog`, the command shall run the script and print the path of the page. (D7)
- R2: The script shall write one HTML file to `.kairyn/backlog.html`, with all CSS, JS and data inline. (D2, D4)
- R3: The page shall load no file and no URL: no external script, stylesheet, font or image. (D5)
- R4: When `.gitignore` has no `.kairyn/backlog.html` line, the script shall append one, and create `.gitignore` if it is missing. (D4)
- R5: The page shall list every idea file, each with its title, appetite, capture date and problem line. (D6)
- R6: The page shall show no idea status: no status groups, chips, labels or filters. (D6)
- R7: When the user types in the search field, the page shall list only ideas whose title, slug or text contains it. (D6)
- R8: When the user picks an appetite, the page shall list only ideas with that appetite. "Not set" lists ideas with none. (D6)
- R9: When the user opens an idea, the page shall show its front matter, full text and log. (D6)
- R10: When an idea's text links to another idea file, the link shall open that idea on the page. (D6)
- R11: Where `docs/backlog/TRIAGE.md` exists, the page shall show its `## Next` and `## Parked` sections in a collapsed block. (D6)
- R12: The script shall turn the markdown into HTML and escape HTML in the idea files. (D5, A1)
- R13: The page shall offer no control that changes an idea. (D3)
- R14: If `docs/backlog/` has no idea file, the script shall print one line that says so, write no page and exit 1. (A2)
- R15: If `.kairyn/` is missing, the script shall tell the user to run `/kairyn:init`, write nothing and exit 1. (A3)
- R16: The page shall follow the system light or dark theme, and fit a 360 px wide screen with no sideways scroll. (request)
- R17: The script shall run on Python 3.9 with the standard library only. (D1, D2)

## Non-functional needs
- Accessibility: each idea opens with the keyboard, and Escape closes the detail view. (A4)
- Performance: not applicable: no source states a need.
- Security: idea text cannot run script on the page. (A1)
- Observability: the script prints the page path, or one error line. (D7)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Raw HTML in an idea file shows as text. Links keep only `http(s)`, relative and `#` targets. | Jayson De los Reyes |
| A2 | assumption | A repo with no idea file gets no page. | Jayson De los Reyes |
| A3 | assumption | The script writes into an initialized repo only, so it never creates `.kairyn/`. | Jayson De los Reyes |
| A4 | assumption | Keyboard use counts as the accessibility need, as in the prototype. | Jayson De los Reyes |
| A5 | assumption | Ideas list newest capture first. | Jayson De los Reyes |
| A6 | assumption | Idea files follow `TRIAGE.md` naming and fields. A missing field shows empty. | Jayson De los Reyes |
| K1 | risk | Evals cost tokens: a new `backlog` eval, and `check` because its `# depends:` covers `plugin/scripts/*`. | Jayson De los Reyes |
| K2 | risk | The appetite is not set. The steward proposes small batch. | Jayson De los Reyes |
| P1 | dependency | Design names the evals, runs and cost before any eval runs. | design |

## Acceptance criteria
- [ ] An eval runs `/kairyn:backlog` in a repo with idea files. The reply names `.kairyn/backlog.html`, and the file exists. (R1)
- [ ] A test finds one `<style>`, one `<script>` with no `src`, and every idea inline. (R2)
- [ ] A test finds no `<link`, `src=`, `@import`, `url(` or `fonts.googleapis` in the page outside the idea text. (R3)
- [ ] Tests run the script with no `.gitignore`, with one that lacks the line, and with one that has it. Each ends with exactly one `.kairyn/backlog.html` line, and other lines stay. (R4)
- [ ] A test builds a page from three idea files and finds each title, appetite, date and problem line. (R5)
- [ ] A test with ideas of each status finds no status word outside the idea text. (R6)
- [ ] A browser check by the owner: search, the appetite filter, open, Escape and an idea-to-idea link work, in light and dark, at 360 px. (R7, R8, R9, R10, R16, A4)
- [ ] A test finds an idea-to-idea link rendered as `#<slug>`. (R10)
- [ ] A test finds the Next and Parked text inside `<details>`, and no other `TRIAGE.md` section. (R11)
- [ ] A test finds `<b>x</b>` in an idea rendered as `&lt;b&gt;x&lt;/b&gt;`, a `javascript:` link dropped, and `</script>` in an idea unable to end the script. (R12, A1)
- [ ] A test finds no `<input>`, `<select>` or `<button>` in the page other than search, the appetite filter, the idea rows and close. (R13)
- [ ] Tests run the script with no idea file and with no `.kairyn/`. Each exits 1, prints one line and writes nothing. (R14, R15)
- [ ] `tests/test_python39.py` runs the script on Python 3.9. (R17)
- [ ] `uv run pytest` and `claude plugin validate plugin` pass, and `plugin.json` has a new version. (R1, R2)

## Open questions and answers
- None. The grill answered the questions as D1-D8 in `CONCEPT.md`. (Jayson De los Reyes)

Approval: Jayson De los Reyes, 2026-11-25T11:45:31Z, "approved REQUIREMENTS.md and assumptions A1-A6 as written"
