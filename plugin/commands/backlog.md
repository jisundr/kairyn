---
description: Build a view-only HTML page of every idea in docs/backlog/ and print its path
model: haiku
allowed-tools: Bash(python3:*)
---

Build the backlog page for the current repository. The script does the work; do not write HTML by hand.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/backlog_html.py --root .` from the repo root.
2. If it exits 0, it printed the page's path. Report that path exactly, and say the user can open it in a browser.
3. If it exits 1, report its line exactly. Do not create files to work around it.
