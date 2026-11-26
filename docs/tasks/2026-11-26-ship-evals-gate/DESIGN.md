---
task: 2026-11-26-ship-evals-gate
stage: design
summary: "Option A: a top-level evals: section (command, paths) in afk.yml; afk.py runs it as the 4th review gate; scripts/evals_gate.py replaces scripts/gates.py."
---

# Design: ship the evals review gate in afk.py

## Approach
Option A. `.kairyn/afk.yml` gets a top-level `evals:` section with `command:` and a `paths:` list of globs. `parse_afk` reads it as it is. `REVIEW_GATES` becomes `design`, `commits`, `sessions`, `evals`, so the gate runs after `sessions` and before `gates:` (R1). `Afk.gate_evals()` takes the changed files after the base, without the task folder and `DESIGN_ALLOW` (A4). It matches them with `path_matches` against `paths:`, or takes any change when `paths:` is empty (R3, R4). Then it runs the command with `Afk.command()` in the code repo, with `KAIRYN_BASE=<base sha>` in its environment, so a command can find the change. A non-zero exit blocks as `gate evals failed: \`<command>\` exited <code>` (R5). With no command, the row is `not set` and the run prints one `NOTE:` line (R2). A child-repo task reads the home `evals:` section and the child's changed files (A3). K1: an `evals:` entry under `gates:` stays a plain command gate; the docs tell a repo to move it, and this repo does (R8).

This repo's command is `python3 scripts/evals_gate.py` (new). It holds `check_evals` from `scripts/gates.py`: base from `KAIRYN_BASE`, else the merge base with `main` (R7).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Top-level `evals:` with `command:` and `paths:`; one gate method | One method, template lines, one small script | Low: same parser, same row format |
| B | A `paths:` map for every `gates:` entry | More config and tests | Not asked; changes each gate |
| C | Ship the `passed.json` check in `plugin/` | A consumer-side record of eval passes | D1 and D4 rule it out |

## Tasks
- T1: Tracer: `gate_evals` runs `evals: command:` when a changed file matches `paths:`, after `sessions`; exit 0 passes, else it blocks; the command gets `KAIRYN_BASE`. Files: `plugin/scripts/afk.py`, `tests/test_afk_review_gates.py`. Done: `uv run pytest tests/test_afk_review_gates.py` exits 0.
- T2: No command: a `not set` row and one `NOTE:` line, and the run goes on. No match: the command does not run, a `pass` row says no path matched. No paths: any code change runs it. Files: as T1. after: T1. Done: `uv run pytest tests/test_afk_review_gates.py` exits 0.
- T3: The template shows `evals:` with empty `command:` and `paths:` and comments; the afk.py docstring and both afk-run docs describe the gate. Bump to 0.19.0 and run `uv run python scripts/release_hashes.py --write`. Files: `plugin/templates/afk.yml`, `plugin/scripts/afk.py`, `plugin/harness/.harness/workflows/afk-run.md`, `.harness/workflows/afk-run.md`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`, `tests/test_afk.py`. after: T2. Done: `uv run pytest` exits 0 and `uv run python plugin/scripts/harness_docs.py` exits 0.
- T4: `scripts/evals_gate.py` (new) with the tests of `tests/test_gates.py` moved to `tests/test_evals_gate.py` (new); delete `scripts/gates.py` and `tests/test_gates.py`; `.kairyn/afk.yml` drops `gates: evals:` and sets `evals:` `command: python3 scripts/evals_gate.py`, `paths: - 'plugin/**'`. Not in `plugin/`: this repo's own check. Files: `scripts/evals_gate.py` (new), `tests/test_evals_gate.py` (new), `scripts/gates.py`, `tests/test_gates.py`, `.kairyn/afk.yml`. after: T1. Done: `uv run pytest` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 command exits 0 on a guarded change: pass, it ran | T1 | pytest: `test_evals_gate_runs_the_command_on_a_guarded_change` |
| AC2 no command: `not set`, one note, run goes on | T2 | pytest: `test_evals_gate_not_set_prints_one_note` |
| AC3 only unguarded files: command not run, pass | T2 | pytest: `test_evals_gate_skips_when_no_path_matches` |
| AC4 command and no paths: it runs | T2 | pytest: `test_evals_gate_with_no_paths_runs_on_any_change` |
| AC5 exit 1: blocks, log names gate, command, code | T1 | pytest: `test_evals_gate_blocks_on_a_failing_command` |
| AC6 template has empty `evals:` and comments; `parse_afk` reads it | T3 | pytest: `test_template_has_an_empty_evals_section` |
| AC7 script: pass at current hash, fail with none, pass with no `plugin/` change | T4 | pytest: `tests/test_evals_gate.py` |
| AC8 `scripts/gates.py`, `tests/test_gates.py` gone; afk.yml sets command and `plugin/**` | T4 | `test ! -e scripts/gates.py && test ! -e tests/test_gates.py`; pytest: `test_repo_afk_yml_sets_the_evals_gate` |
| AC9 docs and docstring name the evals gate; check passes | T3 | `grep -l 'evals' .harness/workflows/afk-run.md plugin/harness/.harness/workflows/afk-run.md`; `/kairyn:check` |
| AC10 after merge, close deletes the idea and its README row | close | `test ! -e docs/backlog/20261125053013-ship-review-gates.md`; `grep -c ship-review-gates docs/backlog/README.md` prints 0 |

Eval plan, 10 runs each, as the selector picks them (`# depends:`). Costs: the last runs named in task logs (split-build-routing, 2026-11-25); real runs come 20-60% above.

| Eval | Why it runs | Last cost at 10 runs |
|---|---|---|
| `build` | `afk.py`, `plugin/harness/**` | $7.45 |
| `review` | `afk.py`, `plugin/harness/**` | $2.82 |
| `gates` | `afk.py`, `plugin/harness/**` | $1.57 |
| `check`, `init`, `upgrade` | scripts, templates, hashes | $0.25 |
| `design` | `plugin/templates/afk.yml`, `plugin/harness/**` | $16.93 |
| `requirements`, `retro` | `plugin/harness/**` only | $15.19, $4.54 |
| Total | | $48.75; $12.09 for build, review, gates, check, init, upgrade |

Approval: Jayson De los Reyes, 2026-11-26T04:18:15Z, "Approve as written"
