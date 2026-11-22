---
task: 2026-11-22-plugin-versioning
stage: requirements
summary: "Consumers record their kairyn version and upgrade safely: manifest, .base/ three-way merge, release hashes, version check, 3 bugs."
---

# Requirements: Plugin versioning and consumer upgrades

## Problem statement

The user asked for a fix to versioning for consumer projects. `/kairyn:init` copies stages, templates and harness docs into a consumer repo once. It records no version or file hashes. A second run prints `ALREADY INITIALIZED` and changes nothing. So a consumer never receives plugin fixes or new stages. The plugin's scripts update but the consumer's copies stay old, so a new script can fail on old files. The repo also cannot tell a file the user edited from a stale default.

## Scope

**In**
- A manifest that init writes: the plugin version and a hash for each installed file.
- A copy of each installed file in `.kairyn/.base/`, as the merge base.
- File ownership. Upgrade replaces plugin-owned files and merges repo-owned files.
  - Plugin-owned: the kairyn `CLAUDE.md` block, the kairyn harness docs (`running-stages.md`, `task-lifecycle.md`, `keeping-docs-lean.md`), `.kairyn/templates/STATE.md`.
  - Repo-owned: `.kairyn/stages/*`, `.harness/README.md`, `.harness/budgets.yml`.
  - Never touched: `.kairyn/learnings.md`, `docs/tasks/`, `CLAUDE.md` outside the kairyn block, the user's own harness docs.
- `/kairyn:upgrade`, backed by a script in `plugin/scripts/`.
- A version check script for `/kairyn:check`, `verify-init.sh` and a `SessionStart` hook.
- Upgrade for repos from before the manifest (v0.1.0, like this repo), with `plugin/release-hashes.json`: the sha256 of every installed file in every release.
- The bugs in A1, and the CI rule in A2.

**Out**
- Migration scripts for breaking changes. They come with the first breaking change.
- A kairyn version field in `STATE.md`.
- Downgrades and pinning a version.
- Init's report not listing the harness docs it created (separate small fix).

## Assumptions

- A1: Three bugs found while installing kairyn in its own repo belong to this task:
  - A repo that already has `.harness/budgets.yml` keeps it, so the budget check fails on the new `.kairyn/` files.
  - `harness_docs.py` refreshes only the first `harness-docs` marker pair in a file.
  - `verify-init.sh` fails once a task exists, so it cannot check a repo in use.
- A2: CI enforces a version bump, so a plugin change always reaches consumers.
- A3: The repo rules apply: tests first, and the init eval still passes.
- A4: Upgrade reports one line per file and writes a conflict to `<file>.kairyn-new`.
- A5: A v0.1.0 fixture with user edits and one task proves the upgrade path.

## Acceptance criteria

- [ ] After init, `.kairyn/manifest.json` holds the plugin version and a sha256 for every installed file. `.kairyn/.base/` holds an exact copy of each. (request)
- [ ] Init still never overwrites. A second run changes nothing. Only `/kairyn:upgrade` changes installed files. (request)
- [ ] Upgrade replaces each plugin-owned file. In `CLAUDE.md` it replaces only the text between `<!-- kairyn:start -->` and `<!-- kairyn:end -->`. (request)
- [ ] For a repo-owned file, upgrade merges base, local file and new file in three ways (request, A4):
  - unchanged locally: upgrade writes the new version;
  - clean merge: upgrade writes the result and keeps the user's edits;
  - conflict: upgrade keeps the local file, writes the merge to `<file>.kairyn-new` and puts no conflict markers in the local file.
- [ ] Upgrade adds files that are new in this version. It never touches `learnings.md`, `docs/tasks/` or the user's own docs. (request)
- [ ] Upgrade prints one line per file (`REPLACED`, `MERGED`, `ADDED`, `CONFLICT`, `KEPT`), updates the manifest and `.base/`, and exits non-zero on any conflict. (A4)
- [ ] A second upgrade in a row changes nothing. (request)
- [ ] Repo with no manifest: upgrade replaces a file that matches the current plugin file or any hash in `release-hashes.json`. A file that matches no release goes through the conflict path. (request)
- [ ] This repo's v0.1.0 stages, which predate the Writing rule, upgrade with `REPLACED` and no `CONFLICT`. (request)
- [ ] A pytest test fails when an installed file's current hash is missing from `release-hashes.json` for the version in `plugin.json`. (request)
- [ ] `/kairyn:check` and `verify-init.sh` report an older manifest version and name `/kairyn:upgrade`. They report nothing when the versions match. (request)
- [ ] The plugin ships a `SessionStart` hook that runs the same check. It prints nothing without `.kairyn/` or when the versions match. It prints one line naming `/kairyn:upgrade` when the plugin is newer. It writes no file, finishes in under 1 second, and passes `claude plugin validate plugin`. (request)
- [ ] `/kairyn:check` passes after init and after upgrade, also in a repo with a strict `.harness/budgets.yml`. (A1)
- [ ] `harness_docs.py --write` refreshes the index inside the kairyn block when a file has more than one marker pair. (A1)
- [ ] `verify-init.sh` passes on a repo with tasks in `docs/tasks/`. Only init keeps the empty `docs/tasks/` check. (A1)
- [ ] The v0.1.0 fixture upgrades to the current version, and `verify-init.sh` passes on it. (A5)
- [ ] CI fails a pull request that changes `plugin/` without a new `plugin.json` `version`. (A2)
- [ ] Each new or changed script has a pytest test that failed first, and the init eval passes. (A3)

## Open questions and answers

1. Which files does the plugin own? **Answered (user):** the split in Scope.
2. Merge strategy for edited files? **Answered (user):** three-way merge using `.kairyn/.base/`.
3. A `SessionStart` hook in this task, or later? **Answered (user):** in this task, warn only.
4. Old files in repos without a manifest? **Answered (user):** recognize them with `release-hashes.json`.
