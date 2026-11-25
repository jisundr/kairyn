---
task: 2026-11-25-backlog-page
stage: grill
summary: "/kairyn:backlog builds one offline, view-only HTML page that indexes every idea file in docs/backlog/."
---

# Concept: A visual index of the backlog

## Concept
`/kairyn:backlog` runs a stdlib Python script in `plugin/scripts/` and prints the path of the page it writes. The page is one self-contained HTML file at `.kairyn/backlog.html`, with all JS, CSS and data inline. It loads nothing from the network, and the script adds it to `.gitignore`. It is a view-only, visual `README.md` for every idea file in `docs/backlog/`: title, appetite, capture date and the first line of the problem. It has search, an appetite filter, a detail view with the full text and log, idea-to-idea links, and the Next and Parked notes of `TRIAGE.md`. It shows no status: tasks track the work.

## Decisions
- D1: Ship it in the plugin for consumer repos, in `plugin/scripts/`. So it needs a version bump, Python 3.9 support and evals. (user)
- D2: A stdlib Python script builds one self-contained HTML file, with JS, CSS and data inline. (user)
- D3: The page is view only. It does not edit status, appetite or any other field. (user)
- D4: The script builds the page on demand and writes it to `.kairyn/backlog.html`. The script adds that path to `.gitignore`. (user)
- D5: The page is fully offline: system fonts, no Google Fonts, no CDN. The script turns the markdown into HTML. (user)
- D6: The page shows no status: no status groups, chips, labels or unknown-status handling. It indexes every idea file, like `README.md` but more visual. Each idea shows its title, appetite, capture date and the first line of its problem. The page has search, an appetite filter, a detail view with full text and log, idea-to-idea links, and the Next and Parked notes of `TRIAGE.md`. (user)
- D7: The command `/kairyn:backlog` runs the script and prints the page's path. (user)
- D8: Drop the repo-only `scripts/backlog_html.py` from WIP commit `c46a131`. Reuse its rendering code, rebuilt tests-first in `plugin/scripts/`. (user)

## Terms
| Term | Meaning |
|---|---|
| idea file | A file `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md` with front matter, as `TRIAGE.md` names it. |
| page | The generated file `.kairyn/backlog.html`. |
| problem line | The first line of the text after the `**Problem...:**` label in an idea file, as plain text. |
| triage notes | The `## Next` and `## Parked` sections of `docs/backlog/TRIAGE.md`. |

## Open branches
- None. The appetite is not set: the steward proposes small batch, and the owner confirms it.

Approval: Jayson De los Reyes, 2026-11-25T11:39:34Z, "Yes, that's it"
