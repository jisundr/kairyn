---
title: Upgrade
summary: "How /kairyn:upgrade, the manifest, release hashes, the version check and the bump rule fit together."
read_when: "changing upgrades or the plugin version"
load: on-demand
---

# Upgrade

A consumer repo keeps the kairyn files it installed. `/kairyn:upgrade` (`plugin/scripts/upgrade.py`) brings them up to the plugin's version without losing the user's edits.

## The record

- `.kairyn/manifest.json`: plugin version, and the sha256 and owner of each installed file. `kairyn_files.py` holds the file table and owners.
- `.kairyn/.base/<path>`: the shipped version the repo last took, the merge base.
- The `CLAUDE.md` block is `CLAUDE.md#kairyn`. Its doc index is left out of its hash, because `/kairyn:check write` refreshes it.
- `plugin/release-hashes.json`: hashes of every installed file in every release, for repos with no manifest (before 0.2.0).

## Rules, per file

| Case | Result |
|---|---|
| Missing | `ADDED` |
| Same as the new version | `KEPT` |
| Plugin-owned (templates, kairyn harness docs, the block) | `REPLACED`; an edited copy goes to `<file>.kairyn-old` |
| Repo-owned (stages, harness README, budgets) and unedited | `REPLACED` |
| Repo-owned and edited | `git merge-file`: `MERGED` or `CONFLICT` |
| No manifest and no release matches | `CONFLICT` |
| A file the user had before init | never touched |
| Recorded, no longer shipped, missing or unedited | `REMOVED`: file, `.base/` copy and entry |
| Recorded, no longer shipped, edited | `CONFLICT`: kept; the user moves the edits and deletes it, then the next upgrade prints `REMOVED` |
| Not recorded, no longer shipped | never touched |

On `CONFLICT` the local file stays and the merge goes to `<file>.kairyn-new`. The user takes what they want and deletes it. The next upgrade marks it resolved. If the conflict had nothing to merge from and they kept their version, the file is theirs from then on. The manifest takes the new version only when no conflict is open.

## Version check

`version_check.py` prints one line naming `/kairyn:upgrade` when the plugin is newer than the manifest. It runs in `/kairyn:check`, in `verify-init.sh` (as `WARN:`) and in the `SessionStart` hook (`plugin/hooks/hooks.json`). It always exits 0.

## Changing installed files

1. Bump `version` in `plugin/.claude-plugin/plugin.json`. CI (`version-bump`, `scripts/check_version_bump.py`) fails a pull request into `main` that changes `plugin/` without a newer version.
2. Run `uv run python scripts/release_hashes.py --write`. A test fails until the hashes are current.
3. Tests: `tests/test_upgrade.py` (fixture `tests/fixtures/consumer-v0.1.0/`), `test_kairyn_files.py`, `test_version_check.py`. Eval: `upgrade`.

- AFK gates do not run CI's `version-bump`: bump the version and run `release_hashes.py --write` before review.
- Upgrade tests that cover a removed shipped file install from a plugin copy that still ships it.
- This repo installs its own plugin: a new shipped harness doc lands in `.harness/workflows/` and needs index rows in `CLAUDE.md` and `.harness/README.md`. Plan the cuts in design.
