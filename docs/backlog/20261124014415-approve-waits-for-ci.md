---
title: afk.py approve merges before CI reports on the new head
status: triaged
date: 2026-11-24
appetite: small batch
requester: Jayson De los Reyes
---

# afk.py approve merges before CI reports on the new head

**Learning (word for word):** - 2026-11-24 [exit] `afk.py approve` pushes a decision commit, then merges at once. The new head has no checks yet, so `gh pr merge` fails. Wait for CI on the new head, then merge.

**Retro action:** backlog: script `plugin/scripts/afk.py`.

# Log

2026-11-24T01:44:15Z [capture] Created by the retro of 2026-11-24 from a learning. Status inbox, waiting for triage.
2026-11-24T02:11:01Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-24T02:11:01Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
