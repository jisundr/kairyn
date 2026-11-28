---
task: 2026-11-28-split-design-stage
stage: design
summary: "Move DESIGN.md steps 6 and 7 to a new plugin/stages/_slices.md; DESIGN.md points to it and drops to about 336 tokens."
---

# Design: Split the design stage

## Approach
Option A. Steps 6 and 7 of `plugin/stages/DESIGN.md` move word for word to a new `plugin/stages/_slices.md` (R2). Step 6 keeps one line: fill the template, and follow `_slices.md` for Tasks and Test plan (R3). Step 7 goes. `DESIGN.md` drops from 456 to about 336 tokens (guess), under 350 (R1). The stage, its output and its approval do not change (R4, R5). `init.sh` copies every file in `plugin/stages/`, so `_slices.md` ships with no script change (A3). No rule is cut, so the reviewer has no cut to check.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Move steps 6 and 7 to `_slices.md`; one pointer line in step 6 | 2 slices, about 10 files | The agent skips `_slices.md` (K1); the design eval shows it |
| B | Put the rules in `plugin/templates/DESIGN.md` as notes | 1 slice | Template is at 148/200 and cannot take 140 tokens; R5 forbids the change |
| C | Put the rules in `plugin/skills/design/SKILL.md` | 1 slice | Skill is at most 300 tokens; a repo edit to `.kairyn/stages/` no longer controls the rules |

## Tasks
- T1: tracer bullet: the move. New tests in `tests/test_static.py` fail first: `DESIGN.md` is at most 350 tokens by `estimate_tokens` and its Steps name `_slices.md`; `_slices.md` holds each moved rule word. Then move the rules. `test_design_cuts_vertical_slices` (`tests/test_static.py`) and `test_slice4_design_marks_approval_slices` (`tests/test_afk.py`) read `_slices.md`. Add `_slices.md` to `# depends:` in `evals/promptfoo/design.yaml`. Name `_slices.md` among the shared files in `.harness/workflows/change-a-stage.md`. Files: `plugin/stages/DESIGN.md`, `plugin/stages/_slices.md` (new), `tests/test_static.py`, `tests/test_afk.py`, `evals/promptfoo/design.yaml`, `.harness/workflows/change-a-stage.md`. Done: `uv run pytest` exits 0.
- T2: release and this repo's copy. Bump `plugin/.claude-plugin/plugin.json` to 0.21.3. Run `uv run python scripts/release_hashes.py --write`. Run `python3 plugin/scripts/upgrade.py --root .` in this repo: `.kairyn/stages/DESIGN.md` is `REPLACED`, `.kairyn/stages/_slices.md` is `ADDED`. Files: `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`, `.kairyn/stages/DESIGN.md`, `.kairyn/stages/_slices.md` (new), `.kairyn/.base/.kairyn/stages/DESIGN.md`, `.kairyn/.base/.kairyn/stages/_slices.md` (new), `.kairyn/manifest.json`, `tests/test_dev_harness.py`. after: T1. Done: `uv run pytest && claude plugin validate plugin` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 `DESIGN.md` at most 350 tokens and names `_slices.md` | T1 | New test in `tests/test_static.py`, red before the move |
| AC2 `_slices.md` holds the moved rule words | T1 | New test in `tests/test_static.py`, red before the move |
| AC3 no change to the 4 protected files | T1, T2 | `git diff --quiet main -- plugin/templates/STATE.md plugin/templates/DESIGN.md plugin/scripts/afk.py evals/checks.py` |
| AC4 3 design scenarios meet `min_pass_rate` at 10 runs | T1 | The evals review gate: `python3 scripts/evals_gate.py` after `/run-evals design` |
| AC5 `design.yaml` depends and `change-a-stage.md` name `_slices.md` | T1 | `grep -q _slices.md evals/promptfoo/design.yaml && grep -q _slices.md .harness/workflows/change-a-stage.md` |
| AC6 newer version, pytest and plugin validate pass | T2 | `uv run pytest && claude plugin validate plugin` |
| AC7 after close, idea gone and an ADR names the rejected split | T2 | Manual: after `/kairyn:close`, check `docs/backlog/` and `docs/adr/` |

Approval: Jayson De los Reyes, 2026-11-28T01:40:41Z, "Approve"
