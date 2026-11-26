---
task: 2026-11-26-ship-evals-gate
stage: grill
summary: "afk.py runs a built-in evals gate: a command and paths from .kairyn/afk.yml; this repo moves its passed.json check to a small script."
---

# Concept: ship the evals review gate in afk.py

## Concept
afk.py runs `evals` as a fourth built-in review gate, so every repo gets it. A repo sets an evals command and the paths it guards in `.kairyn/afk.yml`. The command runs only when a changed file matches those paths, and exit 0 passes. A repo with no evals command gets one note and the gate skips. This repo moves its check (a pass in `evals/results/passed.json` at the current hash) to a small script and deletes `scripts/gates.py`.

## Decisions
- D1: The shipped evals gate runs a command set in `.kairyn/afk.yml`; exit 0 passes. (user, 2026-11-26)
- D2: When a repo sets no evals command, the gate skips and prints one note. (user, 2026-11-26)
- D3: The command runs only when changed files match paths set in `.kairyn/afk.yml`. (user, 2026-11-26)
- D4: This repo's command keeps today's check (`passed.json` matches the current plugin), moved to a small script. (user, 2026-11-26)
- D5: Once shipped, this repo deletes `scripts/gates.py` and uses the built-in gate. (user, 2026-11-26)

## Terms
| Term | Meaning |
|---|---|
| evals gate | The built-in review gate in afk.py that runs the repo's evals command. |
| evals paths | Glob patterns in `.kairyn/afk.yml`; a changed file that matches one makes the command run. |

## Open branches
- None. Source: the owner's grill on 2026-11-26, relayed by an Orca coordinator. Backlog idea `20261125053013-ship-review-gates`.

Approval: Jayson De los Reyes, 2026-11-26T04:10:11Z, "Grill approved: the evals gate runs a command set in afk.yml, exit 0 passes; no command means skip with one note; the command runs only when changed files match paths in afk.yml; this repo's command keeps the passed.json check in a small script; this repo then deletes scripts/gates.py"
