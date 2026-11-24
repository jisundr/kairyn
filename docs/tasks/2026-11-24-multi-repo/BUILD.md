---
task: 2026-11-24-multi-repo
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | d1a8a82 | 1 | a87f569 | 0 |
| T2 | 3e14774 | 1 | b48f86f | 0 |
| T3 | 3e5027b | 1 | 1c08408 | 0 |
| T4 | ab5ce54 | 1 | ee65c88 | 0 |
| T5 | fe5448c | 1 | 8388338 | 0 |
| T6 | 222b634 | 1 | a31efbd | 0 |

## Approvals
Approval T6: Jayson De los Reyes, 2026-11-24T05:44:35Z, "eval passes, approved"

## Flags
- test edit: `evals/promptfoo/design-repo.yaml` in fix
- test edit: `evals/promptfoo/design.yaml` in fix

## Review
- Review 1: `plugin/stages/DESIGN.md` makes changes that are outside DESIGN.md. T6 only says "the design stage writes `repo:`", but the diff also deletes the exit criterion "Each named file exists or is marked `(new)`". It also rewords step 1 ("Ask for requirements approval" becomes "Ask for approval") and changes step 6 from `.kairyn/afk.yml` to `afk.yml`. Dropping the exit criterion removes a check the design stage made before, and no test or eval covers its removal.; The diff adds a new eval file, `evals/promptfoo/design-repo.yaml`, and edits `evals/promptfoo/provider.py` and `evals/promptfoo/asserts.py`. None of these is in T6's file list, which names only `evals/promptfoo/design.yaml`, `evals/runner.py` and `evals/checks.py`. The test plan also says AC11 runs with `/run-evals design`, but the `design_child_repo` scenario is in `design-repo.yaml`, not `design.yaml`, so that command may not run it.
- Review 2, after the fix round: `plugin/stages/DESIGN.md` still has changes outside DESIGN.md that the fix round did not undo. Step 2 drops "(see `_template.md`, Time)". Step 3 drops "Mark new files `(new)`". T6 only says "the design stage writes `repo:`". The exit criterion "Each named file exists or is marked `(new)`" is back, but no step tells the model to mark new files any more, so the stage now asks for something it never told the model to do. No test or eval covers either removal.
