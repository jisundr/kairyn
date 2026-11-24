---
task: 2026-11-24-multi-repo
stage: design
summary: "Option A: a code worktree and code root on afk.py's Run, set from the repos map. Six slices T1-T6 in D8 order."
---

# Design: kairyn tasks in a home repo change code in child repos

## Approach
Option A. `Run` gets `code` (the code worktree) and `code_root` (the repo that holds the code). With no `repo:` line, they are `wt` and `root`, so today's runs do not change (R1). Each call that reads or runs code moves from `wt`/`root` to `code`/`code_root`. Task-file calls stay on `wt` (R4, R6). The child base is the merge base with the child repo HEAD (A2). Reject merges nothing, as today (A5).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `code` and `code_root` on `Run`; code calls use them | About 150 lines in `afk.py`, one test file | A missed `wt` call; the temp-repo tests find it |
| B | A `ChildRun` subclass that overrides each code method | About 250 lines, two copies of logic | The two classes drift apart |
| C | A driver that runs two `Run` objects, home and child | A rewrite of publish and decide | A large change to code that works |

## Tasks
Each slice changes `afk.py`, a stub where it needs one, and its tests. `afk.py` is the only layer, so each slice is vertical through it.
- T1: Tracer bullet: parse the nested `repos:` map, read `repo:`, set `code_root`, block on a bad entry. Files: `plugin/scripts/afk.py`, `tests/test_afk_repos.py` (new). Done: `uv run pytest tests/test_afk.py tests/test_afk_repos.py -q -k "slice or t1"` exits 0.
- T2: Create or reuse `kairyn/<task>` in the child repo as `code`. Task files commit only in `wt`. Files: `plugin/scripts/afk.py`, `tests/test_afk_repos.py`. after: T1. Done: `uv run pytest tests/test_afk.py tests/test_afk_repos.py -q -k "slice or t2"` exits 0.
- T3: Sessions run in `code` with `--add-dir <wt>` and full paths. Red and green checks, flags, diff and backstop use `code` and `code_root`. Files: `plugin/scripts/afk.py`, `tests/stubs/claude`, `tests/test_afk_repos.py`. after: T2. Done: `uv run pytest tests/test_afk.py tests/test_afk_repos.py -q -k "slice or t3"` exits 0.
- T4: Gates and readiness take the child entry's `gates:` and run in `code`. Files: `plugin/scripts/afk.py`, `tests/test_afk_repos.py`. after: T3. Done: `uv run pytest tests/test_afk.py tests/test_afk_repos.py -q -k "slice or t4"` exits 0.
- T5: Publish each repo; post `REVIEW.md` on the child pull request; approve merges child, then home. Files: `plugin/scripts/afk.py`, `tests/stubs/gh`, `tests/test_afk_repos.py`. after: T4. Done: `uv run pytest tests/test_afk.py tests/test_afk_repos.py -q -k "slice or t5"` exits 0.
- T6: (approval) By hand, not AFK: the build stops here. Eval first, then the stage. The design stage writes `repo:`. Add a `repos:` example to the afk.yml template and update `afk-run.md`. Files: `plugin/stages/DESIGN.md`, `plugin/templates/afk.yml`, `.harness/workflows/afk-run.md`, `evals/promptfoo/design.yaml`, `evals/runner.py`, `evals/checks.py`, `tests/test_design_checks.py`. after: T5. Done: `uv run pytest tests/test_design_checks.py tests/test_harness_docs.py -q` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 Current afk.py tests pass unchanged | T1-T5 | `tests/test_afk.py` in each done command |
| AC2 Nested map and today's template parse | T1 | `test_t1_parse_repos`, `test_t1_parse_template` |
| AC3 Unknown name, missing path, non-git path block | T1 | `test_t1_bad_repo_blocks` (three cases) |
| AC4 Task files on home branch, code on child branch | T2 | `test_t2_branches_split` |
| AC5 A second run reuses the child worktree | T2 | `test_t2_reuse_worktree` |
| AC6 Stub records cwd, `--add-dir` and full paths | T3 | `test_t3_session_cwd` |
| AC7 Red and green in the child; approval glob blocks | T3 | `test_t3_red_green_child`, `test_t3_backstop_child` |
| AC8 Child gate runs in child; readiness blocks | T4 | `test_t4_child_gates`, `test_t4_readiness_blocks` |
| AC9 Push and PR per repo; REVIEW.md on child PR | T5 | `test_t5_publish_both` |
| AC10 Child then home merge; child fail blocks | T5 | `test_t5_merge_order`, `test_t5_child_merge_fails` |
| AC11 Design writes `repo:` | T6 | design eval scenario `design_child_repo` (costs tokens; run with `/run-evals design`) |
| AC12 Template and afk-run.md name the map | T6 | `test_harness_docs.py`, then `/kairyn:check` |

Approval: Jayson De los Reyes, 2026-11-24T03:19:40Z, "approved, T1-T5 AFK, T6 by hand"
