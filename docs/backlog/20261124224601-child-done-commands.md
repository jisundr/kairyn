---
title: afk-run.md does not say where child-repo done commands run
status: dropped
date: 2026-11-25
requester: Jayson De los Reyes
---

# afk-run.md does not say where child-repo done commands run

**Learning (word for word):** - design: afk.py runs each done command in a detached checkout of the repo that holds the code (`run_at`). In a child-repo task the done command runs in the child repo, so it must use the child's test tool.

**Retro action:** backlog: KAIRYN-OWNED `.harness/workflows/afk-run.md`.

# Log

2026-11-24T22:46:01Z [capture] Created by the retro of 2026-11-25 from a learning. Status inbox, waiting for triage.
2026-11-24T23:07:13Z [triage] Dropped: merged into shipped-afk-run-child-repos, same file. Decided by Jayson De los Reyes.
