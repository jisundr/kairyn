---
task: 2026-11-23-build-stage
stage: design
summary: "Option A: one stdlib afk.py drives build, gates and review through claude -p, shipped as six vertical slices into the feat/afk-loop branch."
---

# Design: AFK coding loop (build, gates, review)

## Approach
Option A. One Python 3.9 stdlib script, `afk.py`, owns order, limits, checks and git (A1, D7). The model runs only stage files. Six slices, T1 to T6, each merge into the feat/afk-loop branch (D14, D16). T7 is the final pull request to `main`.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `afk.py` calls `claude -p` with a stage file per stage and per `T<n>`. Stubs of `claude` and `gh` test it. | Medium: one script and three stages. | `claude -p` has no turn cap (K2). |
| B | A Stop hook keeps one session looping. | Low code. | One context fills up. The model controls the loop, against D7. |
| C | Claude Agent SDK orchestrator. | High. | Adds a dependency, against A1. |

## Tasks
- T1: Tracer bullet. Add `build`, `gates`, `review` to `stages:`. Design approval sets `stage: build`. Sliced `T<n>` with `after:` in `DESIGN.md`. `afk.py` runs one `T<n>` with red and green checks, one gate, and writes `REVIEW.md`. `/kairyn:review approve` records `Decision:` locally. Add the revert rule. Files: `plugin/scripts/afk.py` (new), `plugin/stages/BUILD.md` (new), `plugin/stages/GATES.md` (new), `plugin/stages/REVIEW.md` (new). Templates: `plugin/templates/BUILD.md` (new), `plugin/templates/GATES.md` (new), `plugin/templates/REVIEW.md` (new). Skills: `plugin/skills/build/SKILL.md` (new), `plugin/skills/review/SKILL.md` (new). Changed: `plugin/templates/STATE.md`, `plugin/stages/DESIGN.md`, `evals/checks.py`, `tests/test_afk.py` (new), `tests/stubs/claude` (new), `.harness/workflows/pull-request.md`. Done: `uv run pytest tests/test_afk.py -k slice1` exits 0.
- T2: Reviewer session with read-only tools and one fix round, then escalation. Test-edit and escape-hatch flags. Findings go to learnings. Retro rule. Files: `plugin/scripts/afk.py`, `plugin/stages/REVIEW.md`, `plugin/stages/RETRO.md`. after: T1. Done: `uv run pytest tests/test_afk.py -k slice2` exits 0.
- T3: Readiness check, cost and time limits. Files: `plugin/scripts/afk.py`, `plugin/templates/afk.yml` (new). after: T1. Done: `uv run pytest tests/test_afk.py -k slice3` exits 0.
- T4: `approval:` patterns, `(approval)` marks in design, the diff backstop, `approve T<n>`. Files: `plugin/scripts/afk.py`, `plugin/stages/DESIGN.md`. after: T3. Done: `uv run pytest tests/test_afk.py -k slice4` exits 0.
- T5: Six ordered gates and `not set`. Files: `plugin/stages/GATES.md`, `plugin/scripts/afk.py`. after: T3. Done: `uv run pytest tests/test_afk.py -k slice5` exits 0.
- T6: Push, `gh pr create`, `gh pr merge`, the no-remote stop. Init and upgrade install `afk.yml`. Files: `plugin/scripts/afk.py`, `plugin/scripts/init.sh`, `plugin/scripts/upgrade.py`, `tests/stubs/gh` (new). after: T5. Done: `uv run pytest tests/test_afk.py -k slice6` exits 0.
- T7: Evals for `build`, `gates`, `review` and the changed `design` and `retro`. README and `.harness/workflows/running-stages.md`. Final pull request to `main`. Files: `evals/promptfoo/build.yaml` (new), `evals/promptfoo/gates.yaml` (new), `evals/promptfoo/review.yaml` (new), `evals/promptfoo/design.yaml`, `evals/promptfoo/retro.yaml`, `evals/runner.py`, `README.md`. after: T6. Done: `uv run pytest` exits 0 and the five evals pass at 10 runs.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 graph order, resume, stop | T1 | `test_afk.py::test_slice1_order_resume` |
| AC2 readiness blocks | T3 | `test_slice3_readiness` |
| AC3 design eval: T1 and `after:` | T1, T7 | `design.yaml` |
| AC4 red check and `BUILD.md` SHAs | T1 | `test_slice1_red_green` |
| AC5 test edit and `# noqa` listed | T2 | `test_slice2_flags` |
| AC6 weak test kept, error read | T7 | `build.yaml` |
| AC7 objection after fix round blocks | T2 | `test_slice2_escalates` |
| AC8 `not set` and failing gate | T5 | `test_slice5_gates` |
| AC9 each limit blocks and logs | T3 | `test_slice3_limits` |
| AC10 approval block and resume | T4 | `test_slice4_approval` |
| AC11 one pull request, approve merges | T6 | `test_slice6_gh` |
| AC12 `REVIEW.md` flags, learnings | T2, T7 | `review.yaml` |
| AC13 init keeps `afk.yml` | T6 | `test_slice6_init` |
| AC14 no remote | T6 | `test_slice6_no_remote` |
| AC15 retro gives `backlog` | T2, T7 | `retro.yaml` |

Approval: Jayson De los Reyes, 2026-11-23T12:45:22Z, "Approve"
