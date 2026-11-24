---
title: Document two AFK-run pitfalls: soft cost cap, hook rewrites
status: triaged
date: 2026-11-24
appetite: small batch
requester: Jayson De los Reyes
---

# Document two AFK-run pitfalls: soft cost cap, hook rewrites

**Learning (word for word):** - build: `claude -p --max-budget-usd` is a soft cap: it stops after the turn that passes it. A $0.01 cap on Opus spent $0.13. It exits 1 with `subtype: error_max_budget_usd`, an empty `result` and the reason in `errors`.

**Retro action:** backlog: KAIRYN-OWNED `.harness/workflows/afk-run.md`.

**Merged (2026-11-24):** hook-rewrites-bash. A user's PreToolUse hook can rewrite Bash commands, so a Bash allowlist stops matching.

# Log

2026-11-24T01:44:15Z [capture] Created by the retro of 2026-11-24 from a learning. Status inbox, waiting for triage.
2026-11-24T02:11:01Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-24T02:11:01Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
2026-11-24T02:11:01Z [merge] Holds hook-rewrites-bash: both are one edit to the shipped afk-run.md. Decided by Jayson De los Reyes.
