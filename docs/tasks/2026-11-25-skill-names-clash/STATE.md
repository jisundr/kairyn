---
task: 2026-11-25-skill-names-clash
title: Skill names clash with built-in commands
stage: build
status: in-progress
stages:
  grill: done
  requirements: done
  design: done
  build: in-progress
  gates: pending
  review: pending
created: 2026-11-24T23:13:12Z
updated: 2026-11-24T23:58:16Z
---

# Log

Newest entry last. One entry per stage run or notable event.

2026-11-24T23:13:12Z [grill] Task created from backlog idea 20261124224610-skill-names-clash. Waiting for answer to Q1.
2026-11-24T23:14:18Z [grill] D1: rename only exit; init and review stay. Waiting for answer to Q2.
2026-11-24T23:14:56Z [grill] D2: new name is close. Waiting for answer to Q3.
2026-11-24T23:15:22Z [grill] D3: rename everything shipped or tested; history stays. Waiting for answer to Q4.
2026-11-24T23:15:50Z [grill] D4: upgrade gets a general removal step. Waiting for answer to Q5.
2026-11-24T23:16:51Z [grill] D5: close.py keeps its subcommands. No open branch. Waiting for concept confirmation.
2026-11-24T23:17:06Z [grill] User confirmed the concept (D1-D5). Next stage: requirements.
2026-11-24T23:18:00Z [requirements] Wrote REQUIREMENTS.md: R1-R10, A1-A5, K1-K3. Waiting for user approval.
2026-11-24T23:18:20Z [requirements] Approved by Jayson De los Reyes. Next stage: design.
2026-11-24T23:20:19Z [design] Wrote DESIGN.md: option A, T1-T4, AC1-AC11. Waiting for user approval.
2026-11-24T23:20:37Z [design] Approved by Jayson De los Reyes. Next stage: build.
2026-11-24T23:29:07Z [build] Blocked: readiness: gate testing exits 1 on the base commit
2026-11-24T23:32:18Z [build] Fixed readiness: REQUIREMENTS.md cut to its 1500-token budget; uv run pytest passes on the base. Resumed.
2026-11-24T23:33:39Z [build] Build started.
2026-11-24T23:56:57Z [build] Blocked: the reviewer still objects after the fix round: `tests/test_dev_harness.py:66` `test_plugin_version_is_0_11_0_or_later` still checks almost nothing, though the fix round raised it. It only checks a version floor. `test_this_repo_kairyn_is_upgraded_to_the_plugin_version`, next to it, already ties the manifest to `plugin_version(PLUGIN)`, and the dogfood test now expects `CLOSE.md`, which only 0.11.0 ships. Remove it, or say why it stays.
2026-11-24T23:58:15Z [build] Fixed the reviewer objection: removed test_plugin_version_is_0_11_0_or_later (decided by Jayson De los Reyes). Resumed.
2026-11-24T23:58:16Z [build] Build started.
