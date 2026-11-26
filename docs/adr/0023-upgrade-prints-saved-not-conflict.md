# 23. Upgrade reports a saved edit with a SAVED line, not a conflict

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-upgrade-overwrites-running-stages. Each upgrade replaced this repo's `.harness/workflows/running-stages.md`, a plugin-owned file, and dropped its `union` note. Workers restored the note by hand in PR #48, #50 and #54. When `upgrade.py` saved the edited copy to `<file>.kairyn-old`, it printed only `REPLACED <file>` and exited 0. Only the `/kairyn:upgrade` command text asked the model to name the `.kairyn-old` file.

## Decision
- The fix has two parts: this repo stops editing the plugin-owned doc, and upgrade warns when it moves an edit aside (D1).
- `upgrade.py` prints one extra line, `SAVED <file>.kairyn-old`, with the next step: move the edits into a file you own, then delete it. It prints no line when it writes no `.kairyn-old`. The exit code stays 0, as for `REPLACED` (D2, R1-R4).
- The `union` note stays only in the `.gitattributes` comment (D3).
- Shipping the union merge to every repo through init is a separate inbox idea (D4).

## Consequences
- A person who runs the script directly sees each moved edit. The command text did not change, so no eval ran (A1).
- A `SAVED` line does not hold back the manifest, and scripts that read the exit code treat it as a clean upgrade.
- An edit to a plugin-owned file still does not survive an upgrade. The user moves it to a file the repo owns.
