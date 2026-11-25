---
title: The milestones watch test is flaky on macOS
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: small batch
review_by: 2027-02-23
---

# The milestones watch test is flaky on macOS

**Raw request:** "Make tests/test_milestones.py::test_watch_local_prints_new_line_and_stores_number reliable on macOS." (Jayson De los Reyes, 2026-11-25, through an Orca coordinator)

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** The test fails now and then on macOS CI, so a red main can be noise. Likely a real bug, not a test flake: `store()` in `plugin/scripts/milestones.py` writes `watch.json` non-atomically.

**Evidence:**
- CI run 45548893428 (main, merge of PR #30, which touched no milestones code), attempt 1: only tests (macos-latest) failed: 1 failed, 639 passed, 2 skipped. Ubuntu passed. Attempt 2 of the same commit passed.
- The failure is `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` at `tests/test_milestones.py:81`, which polls `.session/watch.json`. The text "the watcher printed nothing within 60 s" shows up only in the traceback's source listing. The print assert passed.
- `gh run list --workflow CI -L 20`: three runs failed. Only 45548893428 failed on this test. 45541345484 failed on budget tests, and 45534091999 failed only on version-bump.

**Notes:** `store()` writes `watch.json` with `write_text`, which empties the file before it writes, so a reader can see it empty. Fix: `store()` writes a temp file, then `os.replace`. A `plugin/` change, so evals first. Not a test-only retry on `ValueError`.

# Log

- 2026-11-25T04:58:06Z [capture] Created from the CI failure on main after PR #30. Status inbox, waiting for triage.
- 2026-11-25T05:38:06Z [triage] Kept. Status triaged. Problem confirmed. Decided by Jayson De los Reyes.
- 2026-11-25T05:38:06Z [appetite] Set to small batch. Next. Decided by Jayson De los Reyes.
