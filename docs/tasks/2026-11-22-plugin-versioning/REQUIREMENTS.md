# Requirements: Plugin versioning and consumer upgrades

## Problem statement

`/kairyn:init` copies stages, templates and harness docs into a consumer repo once. It records no version or file hashes, and a second run prints `ALREADY INITIALIZED` and changes nothing. So a consumer never receives plugin fixes or new stages. The plugin's scripts update, but the consumer's copies do not, so a new script can fail on old files. The repo also cannot tell a file the user edited from a stale default, so a safe upgrade is impossible today.

Found while installing kairyn in its own repo:
- A repo that already has `.harness/budgets.yml` keeps it, so the budget check fails on the `.kairyn/` files init just added.
- `harness_docs.py` updates only the first `harness-docs` marker pair in a file. A second pair, such as the one inside the kairyn block, is never refreshed.
- `verify-init.sh` fails once a task exists (`docs/tasks/ should be empty after init`), so it cannot check a repo that is in use or just upgraded.

## Scope

**In**
- A manifest written by init: plugin version and a hash for each installed file.
- A copy of each installed file in `.kairyn/.base/`, used as the merge base.
- File ownership: plugin-owned files are replaced on upgrade. Repo-owned files are merged.
  - Plugin-owned: the kairyn `CLAUDE.md` block, the kairyn harness docs (`running-stages.md`, `task-lifecycle.md`, `keeping-docs-lean.md`), `.kairyn/templates/STATE.md`.
  - Repo-owned: `.kairyn/stages/*`, `.harness/README.md`, `.harness/budgets.yml`.
  - Never touched: `.kairyn/learnings.md`, `docs/tasks/`, `CLAUDE.md` outside the kairyn block, the user's own harness docs.
- `/kairyn:upgrade`, backed by a script in `plugin/scripts/`.
- A version check script, used by `/kairyn:check`, `verify-init.sh` and a plugin `SessionStart` hook.
- Upgrade for repos installed before the manifest existed (v0.1.0, like this repo).
- `plugin/release-hashes.json`: the sha256 of every installed file in every release, so upgrade can recognize an unedited old file.
- The three bugs above.
- A rule that a change under `plugin/` bumps the version in `plugin.json`.

**Out**
- Migration scripts for breaking changes. They come with the first breaking change. The manifest version makes them possible.
- A kairyn version field in `STATE.md`.
- Downgrades and pinning a version.
- Init's report not listing the harness docs it created (separate small fix).

## Acceptance criteria

- [ ] After init, `.kairyn/manifest.json` holds the plugin version and a sha256 for every installed file, and `.kairyn/.base/` holds an exact copy of each.
- [ ] Init still never overwrites. A second run changes nothing, and `/kairyn:upgrade` is the only command that changes installed files.
- [ ] Upgrade replaces each plugin-owned file. In `CLAUDE.md` it replaces only the text between `<!-- kairyn:start -->` and `<!-- kairyn:end -->`.
- [ ] For a repo-owned file, upgrade does a three-way merge of base, local file and new file:
  - unchanged locally: replaced with the new version;
  - clean merge: written with the user's edits kept;
  - conflict: local file untouched, the conflict written to `<file>.kairyn-new`, with no conflict markers in the local file.
- [ ] Upgrade adds files that are new in this version and never touches `learnings.md`, `docs/tasks/` or the user's own docs.
- [ ] Upgrade prints one line per file (`REPLACED`, `MERGED`, `ADDED`, `CONFLICT`, `KEPT`), updates the manifest and `.base/`, and exits non-zero if any file conflicts.
- [ ] Upgrading twice in a row changes nothing the second time.
- [ ] Repo with no manifest: a file that matches the current plugin file or any hash in `release-hashes.json` counts as unedited and is replaced. Only a file that matches no release is treated as user-edited and goes through the conflict path.
- [ ] This repo's v0.1.0 stages, which predate the Writing rule, upgrade with `REPLACED` and no `CONFLICT`.
- [ ] A pytest test fails when an installed file's current hash is missing from `release-hashes.json` for the version in `plugin.json`.
- [ ] `/kairyn:check` and `verify-init.sh` report when the manifest version is older than the plugin and name `/kairyn:upgrade`. They report nothing when the versions match.
- [ ] The plugin ships a `SessionStart` hook that runs the same check. It prints nothing when there is no `.kairyn/` or the versions match. It prints one line naming `/kairyn:upgrade` when the plugin is newer. It never writes a file and finishes in under 1 second. `claude plugin validate plugin` passes with it.
- [ ] `/kairyn:check` passes right after init and after upgrade, even in a repo that already had a strict `.harness/budgets.yml`.
- [ ] `harness_docs.py --write` refreshes the index inside the kairyn block when the file has more than one marker pair.
- [ ] `verify-init.sh` passes on a repo that has tasks in `docs/tasks/`. The fresh-install check (empty `docs/tasks/`) is kept for init only.
- [ ] A test fixture of a v0.1.0 consumer with user edits and one task upgrades to the current version, and `verify-init.sh` passes afterwards.
- [ ] CI fails a pull request that changes `plugin/` without bumping `plugin.json` `version`.
- [ ] Every new or changed script has a pytest test that was seen to fail first, and the init eval still passes.

## Open questions and answers

1. Which files does the plugin own? **Answered (user):** the split above.
2. Merge strategy for edited files? **Answered (user):** three-way merge using `.kairyn/.base/`.
3. Should a `SessionStart` hook warn about a version mismatch in this task, or later? **Answered (user):** in this task. It only warns; upgrade stays manual.
