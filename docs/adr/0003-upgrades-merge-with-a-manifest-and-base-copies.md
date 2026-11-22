# 3. Upgrades merge with a manifest and base copies

Date: 2026-11-22

## Status
Accepted

## Context
Task 2026-11-22-plugin-versioning let consumer repos upgrade the files kairyn installs. The repo owns its stages and edits them. Three options were possible: (A) replace unedited files and report every edited file as a conflict, (B) a manifest, base copies and a three-way merge, (C) read stages live from the plugin, with overrides. Option A makes every edited stage a conflict. Option C takes the stages away from the repo.

## Decision
Option B. `.kairyn/manifest.json` records the version and the hash and owner of each installed file. `.kairyn/.base/` keeps the shipped copy as the merge base. `upgrade.py` replaces plugin-owned files and merges edited repo-owned files with `git merge-file`. A conflict keeps the local file and writes `<file>.kairyn-new`. Repos with no manifest are recognized with `plugin/release-hashes.json`. All logic is Python with no dependencies.

## Consequences
- Every change to `plugin/` needs a version bump. A CI job checks it.
- Each release needs current `release-hashes.json`. A test checks it.
- A `SessionStart` hook warns when the repo is older than the plugin.
- Deleting `<file>.kairyn-new` resolves a conflict.
