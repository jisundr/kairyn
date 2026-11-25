# 18. The backlog page is a script-built, offline, git-ignored file

Date: 2026-11-25

## Status
Accepted

## Context
Task 2026-11-25-backlog-page. To see the backlog, a person reads `README.md`, which lists triaged ideas only, then opens each idea file. The owner asked for a page "used just like readme.md but more visual" that includes every idea. A repo-only prototype (`scripts/backlog_html.py`, WIP commit `c46a131`) built such a page. Three designs were possible: (A) one stdlib script with a command that runs it, (B) as A, with the markdown code in its own module, (C) the command tells the model to write the HTML. B adds a module with no second user. With C, output changes each run and HTML escapes depend on the model.

## Decision
Option A.
- `/kairyn:backlog` ships in the plugin. It runs the stdlib script `plugin/scripts/backlog_html.py`, which runs on Python 3.9 (D1, D7).
- The script writes one self-contained page to `.kairyn/backlog.html`, with JS, CSS and data inline. It builds the page on demand and adds that path to `.gitignore` (D2, D4).
- The page loads nothing from the network: system fonts, no CDN. The script turns the markdown into HTML and escapes HTML in the idea files (D5, A1).
- The page is view only and shows no status. Tasks track the work (D3, D6).
- The repo-only prototype is dropped. Its rendering code was rebuilt test-first (D8).

## Consequences
- The page is never in git. Each user builds it again to see new ideas.
- Tests cover each rule with no model. Only the browser check (AC7) needs a person.
- One file holds parse, markdown and page.
- The script needs `.kairyn/` and at least one idea file. Otherwise it writes nothing and exits 1.
