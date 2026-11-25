---
task: 2026-11-26-split-build-routing
title: Opus makes each critical decision, cheaper models carry it out
stage: build
status: blocked
stages:
  grill: done
  requirements: done
  design: done
  build: pending
  gates: pending
  review: pending
created: 2026-11-25T22:35:13Z
updated: 2026-11-25T23:23:17Z
---

# Log

Newest entry last. One entry per stage run or notable event.

2026-11-25T22:35:13Z [grill] Task created from backlog idea 20261125223513-split-build-routing. The owner's grill on 2026-11-26, relayed by an Orca coordinator, gave D1-D7.
2026-11-25T22:35:13Z [grill] Owner's grill answers recorded as the CONCEPT.md approval. The first fixed-routing work is dropped where it conflicts (D7). Next stage: requirements.
2026-11-25T22:35:13Z [requirements] Wrote REQUIREMENTS.md: R1-R11, A1-A3, K1-K5. Waiting for user approval.
2026-11-25T22:38:44Z [requirements] Approved by Jayson De los Reyes, with A1 and A2 as written (fix rounds on Sonnet). Next stage: design.
2026-11-25T22:38:44Z [design] Wrote DESIGN.md: option A, T1-T7, AC1-AC10, eval plan build, review, gates, close, retro, check, init, upgrade, requirements, design ($50.70 at 10 runs; $18.58 without requirements and design). Waiting for user approval.
2026-11-25T22:41:18Z [design] Approved by Jayson De los Reyes. Next stage: build.
2026-11-25T22:41:18Z [build] Build started by hand from an Orca coordinator dispatch, slices T1-T7 test-first. Evals approved: build, review, gates, close, retro, check, init, upgrade at 10 runs. The owner approved skipping requirements and design: the selector picks them only because the shipped afk-run.md matches plugin/harness/**; their stage, skill and model do not change.
2026-11-25T23:23:17Z [build] T1-T7 green test-first (T6 at 87766e6); uv run pytest 771 passed. Evals run 20261125T230159Z FAIL, cost $14.79: build, review, gates, close, check, init, upgrade PASS; retro on Haiku FAIL (retro_proposes 5/10, retro_applies 7/10). afk_build $7.45 (last all-Opus run $4.67). K1: waiting for the owner's decision on retro.
