---
description: Set up kairyn in this repo (creates .kairyn/ and docs/tasks/)
allowed-tools: Bash(mkdir:*), Bash(cp:*), Bash(ls:*), Bash(bash:*), Read, Write
---

Initialize kairyn in the current repository.

1. If `.kairyn/` already exists, list what is in it and stop. Do not overwrite anything.
2. Create `.kairyn/stages/`, `.kairyn/templates/` and `docs/tasks/` (skip `docs/tasks/` if it exists).
3. Copy every stage file from `${CLAUDE_PLUGIN_ROOT}/stages/` into `.kairyn/stages/` (including `_template.md`), and every file from `${CLAUDE_PLUGIN_ROOT}/templates/` into `.kairyn/templates/`. These copies belong to the repo and may be edited freely.
4. Create `.kairyn/learnings.md` containing only the heading `# Learnings` and a one-line note that stages append here.
5. Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/verify-init.sh .` from the repo root. If it prints any `FAIL:` line, fix the problem and re-run it until it prints `OK`. Do not report success before it does.
6. Report what was created and tell the user the next stage to run is `requirements`. Each task will live in `docs/tasks/<YYYY-MM-DD>-<slug>/` with a `STATE.md`.
