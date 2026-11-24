---
title: Document that a PreToolUse hook can rewrite Bash commands
status: dropped
date: 2026-11-24
appetite: 
requester: Jayson De los Reyes
---

# Document that a PreToolUse hook can rewrite Bash commands

**Learning (word for word):** - build: A user's PreToolUse hook can rewrite Bash commands (rtk turned `git diff` into `rtk git diff`), so an allowlist such as `Bash(git diff:*)` stops matching. A read-only session gets its input in the prompt, not from Bash.

**Retro action:** backlog: KAIRYN-OWNED `.harness/workflows/afk-run.md`.

# Log

2026-11-24T01:44:15Z [capture] Created by the retro of 2026-11-24 from a learning. Status inbox, waiting for triage.
2026-11-24T02:11:01Z [triage] Dropped: merged into max-budget-soft-cap, same doc edit. Decided by Jayson De los Reyes.
