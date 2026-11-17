---
description: Set up kairyn in this repo (creates .kairyn/ with stage definitions)
allowed-tools: Bash(mkdir:*), Bash(cp:*), Bash(ls:*), Read, Write
---

Initialize kairyn in the current repository.

1. If `.kairyn/` already exists, list what is in it and stop. Do not overwrite anything.
2. Create `.kairyn/stages/` and `.kairyn/stones/`.
3. Copy every stage file from `${CLAUDE_PLUGIN_ROOT}/stages/` into `.kairyn/stages/` (including `_template.md`). These copies belong to the repo and may be edited freely.
4. Create `.kairyn/learnings.md` containing only the heading `# Learnings` and a one-line note that stages append here.
5. Report what was created and tell the user the next stage to run is `define`.
