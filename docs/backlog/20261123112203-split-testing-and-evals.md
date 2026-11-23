---
title: testing-and-evals.md has no room for four eval rules
status: triaged
requester: Jayson De los Reyes
date: 2026-11-23
appetite: small batch
review_by:
---

# testing-and-evals.md has no room for four eval rules

**Raw request:** "Accept all" on the triage proposal to merge four retro ideas (Jayson De los Reyes, 2026-11-23, Claude Code session).

**Problem (AI draft, needs a human to confirm):** `.harness/workflows/testing-and-evals.md` is at its 1000-token budget, so four eval rules have no home, and agents repeat the mistakes they record. We would know it improved when the doc is split by topic and all four rules live in the part an agent reads for that work.

**Evidence (merged ideas, quoted word for word):**
- `20261123110952-lint-outputs-by-hand.md`: "To lint a stage output by hand, import `evals/checks.py` with both `evals` and `tests` on `sys.path`: it imports `split_front_matter` from `tests/helpers.py`."
- `20261123110952-judge-sees-every-file.md`: "An LLM judge must see every file the stage could read. The design judge got only `report.py` and scored true README facts as invented (no_invention 2.3)."
- `20261123110952-run-evals-arguments.md`: "`/run-evals` with no arguments runs every eval whose dependencies changed, at 10 runs. `--all-evals` with names runs only those names. For a cheap check, name the eval and add `--runs 2`."
- `20261123110952-fixtures-pass-repo-checks.md`: "An eval fixture must pass the repo's own checks. After adding a harness doc, run `harness_docs.py --write`, or the agent cannot find it."

**Notes:** Retro measured each rule OVER 32 to 45 tokens. Since the small-run gate fix, a 2-run gate needs 2 of 2 passes. The `--runs 2` advice holds: a cheap smoke now fails on any miss.

# Log

2026-11-23T11:22:03Z [triage] Created by merging four retro ideas. Status triaged, appetite small batch. Decided by Jayson De los Reyes.
