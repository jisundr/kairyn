---
task: 2026-11-23-retro
stage: retro
summary: "23 learnings: 6 move to change-a-stage.md, 8 drop, 9 become backlog ideas, 0 keep."
---

# Retro: 2026-11-23

learnings.md before: 1107/1000. After approval: about 10/1000 (heading only).

| Entry | Action | Home or path | Text or reason |
|---|---|---|---|
| L1 | backlog | `.harness/README.md` | OVER 40. `CLAUDE.md` is OVER 40 too, and `keeping-docs-lean.md` is KAIRYN-OWNED. |
| L2 | drop | stale | The upgrade on 2026-11-23 reported KEPT for all three files. The manifest records them. |
| L3 | drop | `.harness/workflows/upgrade.md` | "Its doc index is left out of its hash, because `/kairyn:check write` refreshes it." |
| L4 | move | `.harness/workflows/change-a-stage.md` | Headless `claude -p` refuses Bash pipelines: a globbed `grep` needs approval. Stage steps that must work in evals use Read and Glob. |
| L5 | move | `.harness/workflows/change-a-stage.md` | macOS ignores filename case: `GRILL.md` and `grill.md` are one file. Draft stage and command files in separate folders. |
| L6 | move | `.harness/workflows/change-a-stage.md` | A template that lists every section makes the model fill each one. Write "state only what a source states, else not applicable". |
| L7 | drop | `docs/adr/0004-stage-skills-with-a-model-per-stage.md` | Stale: ADR 0004 chose skills, not generated agents. `MODEL-ROUTING.md` states its target. |
| L8 | drop | `.harness/workflows/running-stages.md` | "The model applies to the turn the skill runs." |
| L9 | drop | `docs/adr/0006-design-is-a-required-stage.md` | "A move to Sonnet needs a 10-run eval pass first." ADR 0004 records the failed Sonnet gate. |
| L10 | move | `.harness/workflows/change-a-stage.md` | `checks.structural_problems` expects requirements to hand off to `design`. A stage after design must change `design_run_problems` and the design eval too. |
| L11 | backlog | `.harness/workflows/testing-and-evals.md` | OVER 38. |
| L12 | backlog | `.harness/workflows/testing-and-evals.md` | OVER 36. |
| L13 | backlog | a test | The home is a test: no function in `evals/checks.py` starts with `test_`. |
| L14 | drop | `evals/checks.py` | `grounded_problems` accepts a path that carries `(new)` anywhere in the text. |
| L15 | backlog | `plugin/stages/_template.md` | `CLAUDE.md`: evals before instructions. |
| L16 | drop | stale | `_template.md` Writing now bans hedges "not even quoted from the request". |
| L17 | move | `.harness/workflows/change-a-stage.md` | A line in `_template.md` Writing changes every stage. Run all its dependent evals at 10 runs. |
| L18 | backlog | `.harness/workflows/testing-and-evals.md` | OVER 45. |
| L19 | move | `.harness/workflows/change-a-stage.md` | Give every stage output a template. Read the failure reasons before you blame the model. |
| L20 | drop | `.harness/budgets.yml` | It sets 1000 tokens. `plugin/scripts/budgets.py` sets the built-in 2000. |
| L21 | backlog | `evals/run.py` | The home is a script: the gate needs `floor(runs × rate)` passes. |
| L22 | backlog | `.harness/workflows/testing-and-evals.md` | OVER 32. |
| L23 | backlog | `.claude/agents/eval-runner.md` | `CLAUDE.md`: evals before instructions. |

Four backlog ideas (L11, L12, L18, L22) wait on room in `testing-and-evals.md`. One idea to split that doc makes room for all four.

Approval: Jayson De los Reyes, 2026-11-23T11:09:52Z, "approved, commit and open a PR"
