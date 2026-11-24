---
title: The shipped afk-run.md does not describe child repos
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: small batch
review_by: 2027-02-23
---

# The shipped afk-run.md does not describe child repos

**Problem (AI draft, needs a human to confirm):** `.harness/workflows/afk-run.md` has a "Code in a child repo" section since 0.10.0. The copy that consumers get, `plugin/harness/.harness/workflows/afk-run.md`, has none. A cerna-home user reads no doc for the `repos:` map.

**Evidence:** Task 2026-11-24-multi-repo R15 named only the repo's own doc.

**Merged (2026-11-25):** child-done-commands. A child-repo task runs each done command in a checkout of the child repo.

# Log

2026-11-24T22:43:54Z [capture] Created by the exit of 2026-11-24-multi-repo. Status inbox, waiting for triage.
2026-11-24T23:07:13Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-24T23:07:13Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
2026-11-24T23:07:13Z [merge] Holds child-done-commands: both are notes for the shipped afk-run.md. Decided by Jayson De los Reyes.
