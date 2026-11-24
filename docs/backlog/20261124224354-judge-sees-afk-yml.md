---
title: The design quality judge does not see afk.yml
status: inbox
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by: 2027-02-23
---

# The design quality judge does not see afk.yml

**Problem (AI draft, needs a human to confirm):** The design eval judge gets the request and requirements, not the fixture's `.kairyn/afk.yml`. A design that states the empty `testing` gate from that file gets a lower `no_invention` score, although the fact is true.

**Evidence:** Run 20261124T045044Z: the two lowest-scored runs were docked for "The `afk.yml` testing gate is empty." 7 of 10 designs in the baseline run 20261123T205538Z state the same fact.

# Log

2026-11-24T22:43:54Z [capture] Created by the exit of 2026-11-24-multi-repo. Status inbox, waiting for triage.
