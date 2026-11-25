---
description: Cut a release from CHANGELOG.md's Unreleased section and tag it locally (never pushes)
argument-hint: "<version>"
model: haiku
allowed-tools: Bash(python3:*), Read
---

Cut a release. The script does the work; do not edit `CHANGELOG.md` or tag by hand.

1. If no version was given, ask for one and stop.
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/close.py release $ARGUMENTS` from the repo root.
3. Report every line it prints exactly. On `FAIL:`, stop.
4. Tell the user to commit `CHANGELOG.md` and push the tag with the command it printed. Do not push it yourself.
