---
description: Set up kairyn in this repo (creates .kairyn/ and docs/tasks/)
allowed-tools: Bash(bash:*), Read
---

Initialize kairyn in the current repository. The work is done by scripts; do not copy files by hand.

1. Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/init.sh .` from the repo root.
   - If it prints `ALREADY INITIALIZED`, tell the user what is in `.kairyn/` and stop. Do not overwrite anything.
2. Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/verify-init.sh .`. If it prints any `FAIL:` line, report the failures exactly and stop. Do not report success before it prints `OK`.
3. Report what was created and tell the user the next stage to run is `requirements`. Each task will live in `docs/tasks/<YYYY-MM-DD>-<slug>/` with a `STATE.md`.
