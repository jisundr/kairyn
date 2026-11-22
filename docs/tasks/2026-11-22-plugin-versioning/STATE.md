---
task: 2026-11-22-plugin-versioning
title: Plugin versioning and consumer upgrades
stage: build
status: done   # in-progress | blocked | done
stages:
  requirements: done   # pending | in-progress | done
  design: done
  build: done
created: 2026-11-21T23:11:54Z
updated: 2026-11-22T07:30:43Z
---

# Log

Newest entry last. One entry per stage run or notable event.

2026-11-21T23:11:54Z [requirements] Task created. Let consumer repos record their kairyn version and upgrade without losing their edits.
2026-11-21T23:12:18Z [requirements] Wrote REQUIREMENTS.md: 15 acceptance criteria for manifest, .base/ three-way upgrade, version check and 3 bugs. Blocked: waiting on the user about the SessionStart hook.
2026-11-21T23:13:12Z [requirements] User answered: SessionStart hook is in scope (warn only). 16 acceptance criteria, no open questions. Last stage, so the task is done; design has no stage yet.
2026-11-21T23:28:44Z [requirements] User added release-hashes.json, so upgrade replaces unedited old files instead of reporting conflicts. 18 acceptance criteria.
2026-11-21T23:33:24Z [design] Wrote DESIGN.md by hand from playbook 02: option B, 8 tasks in 3 pull requests, a test for every criterion. Blocked: waiting on the user to approve the plan.
2026-11-22T00:12:15Z [design] Added identity front matter to REQUIREMENTS.md and DESIGN.md by hand (#5). Still blocked: waiting on the user's change to the design.
2026-11-22T00:35:40Z [requirements] Rewrote REQUIREMENTS.md to the current stage rules (#5, #6): active voice, assumptions A1 to A5, a source on all 18 criteria. Scope did not change.
2026-11-22T05:36:35Z [design] Added two fixes after #7: release hashes for every 0.1.0 commit, and MODEL-ROUTING.md in the file table. Still blocked: waiting on the user to approve the plan.
2026-11-22T05:38:01Z [design] User approved the plan. Build starts by hand from playbook 03 (no build stage yet), task 1: budget and index-marker fixes.
2026-11-22T05:39:51Z [build] Task 1 done: fallback budgets for installed files (also the 3 kairyn harness docs and .harness/README.md, which the design missed), .kairyn/.base/ skipped, every index marker pair refreshed. 164 tests pass.
2026-11-22T05:48:42Z [build] Task 3 done: verify-init.sh default mode accepts tasks and edited stages, --fresh keeps the init checks (init command, CI, init eval). Manifest check waits for task 2. 175 tests pass.
2026-11-22T06:12:03Z [build] Task 2 done: kairyn_files.py (file table, owners, manifest, .base/), init.sh records what it wrote (not files the user had), verify-init.sh checks the manifest. Works on python3 3.9. 202 tests pass.
2026-11-22T06:22:27Z [build] Task 4 done: scripts/release_hashes.py builds plugin/release-hashes.json from every commit per version (0.1.0: 34 hashes, 12 paths) plus the working tree; plugin.json is 0.2.0. 213 tests pass.
2026-11-22T07:02:44Z [build] User decided: deleting <file>.kairyn-new resolves a conflict (the design had no resolution step). A conflict with no merge base, kept by the user, makes the file theirs.
2026-11-22T07:02:44Z [build] Tasks 5 to 8 done: upgrade.py and /kairyn:upgrade, version_check.py (check, verify-init, SessionStart hook), CI version-bump job, upgrade eval. This repo upgraded: 2 stages REPLACED, MODEL-ROUTING.md ADDED, 3 own dev docs resolved as theirs. 253 tests pass.
2026-11-22T07:30:43Z [build] Done. Merged as #8 (design, tasks 1 and 3) and #9 (0.2.0: tasks 2, 4 to 8; #12 folded in). Main CI passed; this repo verifies on 0.2.0.
