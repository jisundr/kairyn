---
title: /kairyn:exit shares its name with the built-in /exit
status: inbox
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by: 2027-02-23
---

# /kairyn:exit shares its name with the built-in /exit

**Raw request:** "I also want to change exit because there is also a command exit." (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (AI draft, needs a human to confirm):** Claude Code has a built-in `/exit` that ends the session. A user who types `/exit` for the kairyn stage quits Claude. Other names can clash too: `init` is a built-in, and `/review` can be one.

**Evidence:** About 24 files name the exit stage: the skill, `plugin/stages/EXIT.md`, `plugin/scripts/exit.py`, `[exit]` log tags, `evals/promptfoo/exit.yaml` and tests. Consumer repos hold `.kairyn/stages/EXIT.md`, and upgrade has no rename step.

# Log

2026-11-24T22:46:10Z [capture] Created by the exit of 2026-11-24-multi-repo from a user request. Status inbox, waiting for triage.
