# 21. The evals gate runs a repo command, guarded by paths

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-ship-evals-gate, the last slice of backlog idea ship-review-gates. afk.py ran the `design`, `commits` and `sessions` review gates for every repo. The `evals` gate was only in this repo's `scripts/gates.py`, and it read this repo's `evals/results/passed.json`. Other repos had no evals gate and no shared way to record eval passes.

## Decision
- afk.py runs `evals` as a built-in review gate after `sessions`. It runs the `command:` of a top-level `evals:` section in `.kairyn/afk.yml`; exit 0 passes (D1).
- With no command, the gate is `not set`: the run prints one note and goes on (D2).
- The command runs only when a changed file matches a glob in `evals: paths:`; with no paths, any change runs it. The command gets `KAIRYN_BASE`, the base commit (D3, A1).
- The plugin ships no eval-pass record. This repo's command is `scripts/evals_gate.py`, which keeps the `passed.json` check; `scripts/gates.py` is gone (D4, D5).
- Rejected: a `paths:` map for every `gates:` entry (not asked); shipping the `passed.json` check in `plugin/` (D1, D4).

## Consequences
- Each repo chooses its own evals check. A repo that sets none gets a note, not a block.
- A child-repo task uses the home `evals:` settings against the child's changed files (A3).
- An `evals:` entry left under `gates:` runs as a plain command gate; the docs tell a repo to move it.
- `/kairyn:upgrade` does not add `evals:` to an existing `.kairyn/afk.yml`; repos learn it from the template (A2).
