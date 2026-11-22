---
description: Check this repo's harness docs and size budgets (add "write" to refresh index tables)
argument-hint: "[write]"
model: haiku
allowed-tools: Bash(python3:*), Read
---

Run the kairyn checkers on the current repository. Use the scripts; do not check by hand.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/harness_docs.py --root .`. If the argument is `write`, add `--write` so it regenerates the index tables first.
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/budgets.py --root .`.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/version_check.py --root .`. If it prints a line, report it as is.
4. Report every `FAIL:` line exactly. For a header or index failure, name the doc and the missing or wrong field. For an over-budget file, suggest cutting or splitting it; do not raise the limit.
5. If both checkers print `OK`, say so in one line.
