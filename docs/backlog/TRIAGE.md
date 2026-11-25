# Triage

Each file is one idea, named `<YYYYMMDDHHMMSS>-<slug>.md` from its capture time (UTC). Status: `inbox` → `triaged` → `shaping` → `shaped` → `committed`, or `parked` / `dropped`. Agents capture and draft; a human triages, sets the appetite and commits.

The index of triaged ideas is [README.md](README.md). Next and Parked were decided by Jayson De los Reyes, 2026-11-25.

## Next

One small batch: atomic-state-md, a shared atomic-write helper for `milestones.store()` and `afk.py` `Task.update()` (evals first).

The atomic `watch.json` write (flaky-watch-test-macos) shipped.

The earlier batches shipped: the afk.py fixes in #31, the gates and lint rules in #30. ship-review-gates is big and needs shaping first.

## Parked

Reviewed by 2027-02-23: release-stage, parallel-slices, pir-stage (needs release-stage), hedge-words-in-backticks, shared-harness-docs, required-checks-app-id, grill-reads-private-notes, several-child-repos, ops-task-close (needs backlog-stage), rerecord-hook-fixtures, grill-reads-other-repo-sessions (with grill-reads-private-notes).
