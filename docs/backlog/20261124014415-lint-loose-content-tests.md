---
title: Lint rule: content tests that match loose words
status: triaged
date: 2026-11-24
appetite: small batch
requester: Jayson De los Reyes
---

# Lint rule: content tests that match loose words

**Learning (word for word):** - review: Ban content tests that match loose words anywhere in a file, with a lint rule on test asserts, because the CONTRIBUTING.md and SECURITY.md tests pass with the rules removed.

**Retro action:** backlog: lint rule in `tests/`.

**Narrowed (2026-11-24):** Tighten the 2 loose tests in `tests/test_github_files.py`. No general lint rule.

# Log

2026-11-24T01:44:15Z [capture] Created by the retro of 2026-11-24 from a learning. Status inbox, waiting for triage.
2026-11-24T02:11:01Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-24T02:11:01Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
2026-11-24T02:11:01Z [shape] Narrowed: tighten the CONTRIBUTING.md and SECURITY.md content tests, no general lint rule. Decided by Jayson De los Reyes.
