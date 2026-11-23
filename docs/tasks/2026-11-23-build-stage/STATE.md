---
task: 2026-11-23-build-stage
title: AFK coding loop from approved design to merge (build, gates, review)
stage: design
status: done   # in-progress | blocked | done
stages:
  grill: done
  requirements: done   # pending | in-progress | done
  design: done
created: 2026-11-23T11:38:32Z
updated: 2026-11-23T12:45:22Z
---

# Log

Newest entry last. One entry per stage run or notable event.

2026-11-23T11:38:32Z [grill] Task created from backlog idea build-stage. Waiting for the answer to Q1.
2026-11-23T11:41:56Z [grill] D1: build proves each T<n> done condition by a command that exits 0. D2: build runs AFK to an open PR, with a build-and-review loop. Waiting for Q2.
2026-11-23T11:44:08Z [grill] D3: inner test-first loop per T<n>, one reviewer subagent pass with one fix round. D4: scope adds gates and review-and-merge stages. Waiting for Q3.
2026-11-23T11:45:26Z [grill] User asked to read the knowledge-base HITL and AFK notes before Q3. Read them. Q3 recommendation changed. Waiting for Q3.
2026-11-23T11:47:10Z [grill] D5: design approval starts AFK; one planned stop at merge; early stops for approval gates, fix-round cap, limits or wrong plan. D3 changed to escalate. Waiting for Q4.
2026-11-23T11:49:41Z [grill] D6: three chained stages build, gates, review, each with its own file and eval. Waiting for Q5.
2026-11-23T11:53:47Z [grill] D7: afk.py runs the loop in a worktree, one headless claude -p per stage, resumes from STATE.md. Waiting for Q6.
2026-11-23T11:55:45Z [grill] D8: limits in .kairyn/afk.yml: per-stage and per-run cost caps, 3 attempts per T<n>, 60 min per stage; a limit blocks with evidence. Waiting for Q7.
2026-11-23T11:56:41Z [grill] D9: ordered gates list with commands in afk.yml; exit code decides; empty command is not set, never a pass. Waiting for Q8.
2026-11-23T11:57:55Z [grill] D10: approval path patterns in afk.yml; design marks (approval) tasks; build stops before them; afk.py diff check as backstop. Waiting for Q9.
2026-11-23T11:59:20Z [grill] D11: script pushes and opens PR; review posts REVIEW.md; /kairyn:review approve or reject records Decision and merges with gh. Waiting for Q10.
2026-11-23T12:01:24Z [grill] D12: test and feat commit per T<n>; script runs red and green checks and flags later test edits. Waiting for Q11.
2026-11-23T12:03:00Z [grill] User linked Q11 to the knowledge-base vertical slices and tracer bullets note. Q11 widened to cover how design cuts T<n>. Waiting for Q11.
2026-11-23T12:05:22Z [grill] D13: design cuts T<n> as vertical slices with T1 the tracer bullet and after: blockers; build runs one claude -p per T<n> in sequence. Waiting for Q12.
2026-11-23T12:07:16Z [grill] D14: this task ships as six stacked PRs, one vertical slice each, in one task folder. Waiting for Q13.
2026-11-23T12:09:44Z [grill] D14 changed: six PRs, each merged to main before the next slice; no stacks. D15: the AFK loop opens one PR per task. Waiting for Q14.
2026-11-23T12:15:07Z [grill] D16: slice PRs target feat/afk-loop with merge commits; one final PR to main after final checks; revert-the-revert rule in pull-request.md. Waiting for Q15.
2026-11-23T12:16:21Z [grill] D17: pytest on afk.py with a stub claude; 10-run evals per stage plus two behavioural fixtures. No open branches. Waiting for concept confirmation.
2026-11-23T12:20:04Z [grill] User asked to check the Lauren Tan note (All Code Is Slop Except Mine) before confirming. Three new branches opened. Waiting for Q16.
2026-11-23T12:26:06Z [grill] D18: readiness check before the first stage: testing gate set, gates green on base, clean worktree. Waiting for Q17.
2026-11-23T12:26:56Z [grill] D19: escape_hatches patterns in afk.yml; script scans added lines; reviewer asks to remove or justify; remaining hits shown at merge stop. Waiting for Q18.
2026-11-23T12:27:48Z [grill] D20: review writes unresolved findings to learnings as constraints; retro sends code corrections to backlog as lint rules or gates. No open branches. Waiting for concept confirmation.
2026-11-23T12:30:00Z [grill] User confirmed the concept (D1 to D20). TL;DR request captured as a backlog idea. CONCEPT.md cut to its 1500-token budget. Next: requirements.
2026-11-23T12:34:15Z [requirements] Wrote REQUIREMENTS.md: R1 to R18 from D1 to D20, 15 criteria. Blocked: waiting for approval in chat.
2026-11-23T12:40:23Z [requirements] Approved by Jayson De los Reyes. Next: design.
2026-11-23T12:42:00Z [design] Wrote DESIGN.md: option A (stdlib afk.py), T1 to T7 as vertical slices, 15 test plan rows. Blocked: waiting for approval in chat.
2026-11-23T12:45:22Z [design] Approved by Jayson De los Reyes. Design is the last stage: status done. Next: build T1 by hand on a slice branch from the feat/afk-loop branch.
