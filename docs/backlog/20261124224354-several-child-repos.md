---
title: A home-repo task can change only one child repo
status: inbox
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by: 2027-02-23
---

# A home-repo task can change only one child repo

**Problem (AI draft, needs a human to confirm):** Task 2026-11-24-multi-repo supports one child repo per task (D1). A task that changes cerna-ui and cerna-bff together still needs a hand-steered build. Changes across repos also need the contract gate from the quality gates playbook (gate 2).

**Evidence:** CONCEPT.md D1 of 2026-11-24-multi-repo put several child repos and the contract gate out of scope.

# Log

2026-11-24T22:43:54Z [capture] Created by the exit of 2026-11-24-multi-repo. Status inbox, waiting for triage.
