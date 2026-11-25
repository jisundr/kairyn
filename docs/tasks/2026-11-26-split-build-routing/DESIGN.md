---
task: 2026-11-26-split-build-routing
stage: design
summary: "afk.py runs build-tests (Opus) then build-code (Sonnet) per slice, each named by its prompt; red check between; close and retro on Haiku."
---

# Design: Opus makes each critical decision, cheaper models carry it out

## Approach
Option A. `build()` in `plugin/scripts/afk.py` calls `self.claude` twice per slice, with the roles `build-tests` and `build-code` (A3). The prompt names the part: `tests part` or `code part`. Between the two, `afk.py` finds `test(T<n>)` and runs the red check, so a bad test stops the slice before Sonnet runs (R2, R3). A red test commit with no green row skips the tests part (R6, A1). The fix round uses `build-code` (R7, A2).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Two fresh `claude -p` sessions per slice; afk.py checks between them | About 40 lines in afk.py, the stub learns the two parts | Context is read twice per slice (K2) |
| B | As A, plus a note from build-tests to build-code | A file per slice | It can disagree with the test |
| C | Opus writes the test, then `claude --resume <id> --model sonnet` writes the code | Context read once | Not shown that a resume changes model |

## Tasks
- T1: Tracer bullet: `MODELS = {"build-tests": "opus", "build-code": "sonnet", "reviewer": "opus", "gate": "sonnet", "review": "opus"}`. `build()` runs the tests part, the red check, then the code part. The stub makes only `test(T<n>)` for a `tests part` prompt and only `feat(T<n>)` for a `code part` prompt. Files: `plugin/scripts/afk.py`, `tests/stubs/claude`, `tests/test_afk.py`. Done: `uv run pytest tests/test_afk*.py` exits 0.
- T2: A tests part with no `test(T<n>)` commit (new stub mode `no_test`), or a test that passes there (`no_red`), blocks with `T<n>` and starts no code part. Files: `plugin/scripts/afk.py`, `tests/stubs/claude`, `tests/test_afk.py`. after: T1. Done: `uv run pytest tests/test_afk.py` exits 0.
- T3: Resume: a red `test(T<n>)` commit after the base and no green row starts only the code part. Files: `plugin/scripts/afk.py`, `tests/test_afk.py`. after: T1. Done: `uv run pytest tests/test_afk.py` exits 0.
- T4: The fix round runs as `build-code`. A test reads the `--model` of the fix-round, reviewer, gate-check and review calls from `stub.log.args`. Files: `plugin/scripts/afk.py`, `tests/test_afk.py`. after: T1. Done: `uv run pytest tests/test_afk.py` exits 0.
- T5: `plugin/stages/BUILD.md`: the tests part does steps 1-3, the code part steps 4-6 and changes no test file. The `afk_build_test_first` assert reads both sessions: the tests session ran the test red and wrote no `textstats.py`; the code session wrote it. Files: `plugin/stages/BUILD.md`, `evals/promptfoo/asserts.py`, `tests/test_afk.py`. after: T1. Done: `uv run pytest` exits 0.
- T6: close and retro on Haiku, each skill model pinned. Done at `87766e6` (the pin test failed first). No new commit. Files: `plugin/skills/close/SKILL.md`, `plugin/skills/retro/SKILL.md`, `tests/test_skills.py`. Done: `uv run pytest tests/test_skills.py` exits 0.
- T7: Docs and release: the `afk.py` docstring and both `afk-run.md` docs name the two parts and models, with cuts to stay in budget (K3). Run `release_hashes.py --write` and `/kairyn:upgrade` for this repo's `.kairyn/` (0.17.0). Files: `plugin/scripts/afk.py`, `.harness/workflows/afk-run.md`, `plugin/harness/.harness/workflows/afk-run.md`, `plugin/release-hashes.json`, `.kairyn/manifest.json`, `.kairyn/stages/BUILD.md`, `.kairyn/.base/` (new copies). after: T2, T3, T4, T5. Done: `uv run pytest` and `claude plugin validate plugin` exit 0.

Eval plan, 10 runs each, as the selector picks them (`# depends:`). Costs: the last 10-run `summary.md` on disk (main checkout, 2026-11-23 and 2026-11-24).

| Eval | Why it runs | Scenarios | Last cost at 10 runs |
|---|---|---|---|
| `build` | `afk.py`, `BUILD.md`, `plugin/harness/**` | `afk_build` | $4.67 (all Opus) |
| `review` | `afk.py`, `plugin/harness/**` | `afk_review` | $2.82 |
| `gates` | `afk.py`, `plugin/harness/**` | `afk_gates_pass`, `afk_gates_fail` | $1.57 |
| `close` | close and retro skills | `close_decision`, `close_plain`, `close_retro` | $4.73 (Sonnet) |
| `retro` | retro skill, `plugin/harness/**` | `retro`, `retro_approval` | $4.54 (Sonnet) |
| `check`, `init`, `upgrade` | scripts, stages, hashes | 5 | $0.25 |
| `requirements` | `plugin/harness/**` only | 3 | $15.19 |
| `design` | `plugin/harness/**` only | 3 | $16.93 |
| Total | | 20 | $50.70; $18.58 without requirements and design |

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 two sessions per slice, Opus then Sonnet, each names its commit | T1 | `test_build_runs_tests_part_on_opus_then_code_part_on_sonnet` |
| AC2 no test commit, or a test that passes: block, no code part | T2 | `test_build_blocks_before_code_without_a_red_test` (parametrized: `no_test`, `no_red`) |
| AC3 no feat commit or a failing green check blocks; a green slice gets its row | T1 | existing `test_slice1_*` build tests |
| AC4 resume with a red test commit starts only the code part | T3 | `test_resume_with_red_test_runs_only_the_code_part` |
| AC5 fix round Sonnet, reviewer Opus, gate Sonnet, review Opus | T4 | `test_afk_roles_run_on_their_models` |
| AC6 BUILD.md names both parts; code part changes no test file | T5 | `test_build_stage_names_tests_and_code_parts` |
| AC7 each skill model pinned | T6 | `test_skill_runs_on_its_routed_model` |
| AC8 `build` at 0.9 or more per metric with cost; `close` and `retro` pass on Haiku | T5, T6 | Evals `build`, `close`, `retro` (plan above) |
| AC9 `/kairyn:check` passes; the three docs name the parts and models | T7 | `/kairyn:check`; `test_afk_docs_name_build_parts` |
| AC10 pytest, validate, version bump | T7 | `uv run pytest`, `claude plugin validate plugin`, `python3 scripts/check_version_bump.py origin/main` |

Approval: Jayson De los Reyes, 2026-11-25T22:41:18Z, "approved DESIGN.md as written"
