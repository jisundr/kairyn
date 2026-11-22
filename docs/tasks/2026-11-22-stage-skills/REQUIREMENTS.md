---
task: 2026-11-22-stage-skills
stage: requirements
summary: "Ship one skill per stage, each with its own model, and record the cost of each eval run."
---

# Requirements: stage skills with a model per stage

## Problem statement

The request is "making agent skills per stages with model routing". The project has spent about $400 in tokens so far (user). Every stage and every eval runs on the session model. `KAIRYN_MODEL` is unset by default, and no run records its cost. So nobody can see which stage or eval spent the money, and each new run costs the same.

## Grounding

- `plugin/` has `commands/` (init, check, upgrade, grill) and no `skills/`. `requirements` and `model-routing` have no command.
- Claude Code skills and commands accept `model:` in front matter. It applies to the rest of that turn, then the session model resumes (code.claude.com/docs/en/skills.md).
- `claude -p --output-format json` returns `total_cost_usd` per run (code.claude.com/docs/en/headless.md).
- `evals/runner.py` passes `--model` only when `KAIRYN_MODEL` is set. The judge uses `KAIRYN_JUDGE_MODEL` or `KAIRYN_MODEL`.
- Agents playbook: skills, not new agents. A model per stage is not a reason for a subagent.

## Scope

In:
- One skill per built-in stage in `plugin/skills/<stage>/SKILL.md`, with a `model:` value. (request)
- `model:` on the commands that only run scripts: init, check, upgrade. (request, A4)
- Cost per eval run in `evals/results/<run-id>/summary.md`. (request, A6)
- Docs, budgets and a version bump that the repo rules require. (A7)

Out:
- Subagents per stage. The playbook rejects them for this reason (Q1).
- Skills for user-added stages. They still run by "follow `.kairyn/stages/<STAGE>.md`".
- Runtime routing from the `model-routing` stage. kairyn makes no LLM API calls.
- A cost target in dollars. No source states one (A5).

## Requirements
- R1: The plugin shall ship a skill for each of `requirements`, `grill` and `model-routing`. (request)
- R2: Each stage skill shall tell Claude to follow `.kairyn/stages/<STAGE>.md` and shall copy no stage steps. (A1)
- R3: Each stage skill shall name its model in a `model:` front matter key. (request)
- R4: When `.kairyn/stages/<STAGE>.md` is missing, the skill shall tell the user to run `/kairyn:upgrade` and stop. (A2)
- R5: The init, check and upgrade commands shall name a `model:` value. (A4)
- R6: When an eval run ends, `summary.md` shall show the cost in USD per scenario and in total. (A6)
- R7: Where a stage runs without its skill, the stage shall work as it does today. (A3)

## Non-functional needs
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a latency need.
- Security: not applicable: no new permissions. `allowed-tools` stays as narrow as `commands/grill.md`.
- Observability: cost per eval scenario and run (request, R6).

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Skills point at the repo's stage file, so a stage edit takes effect with no new skill. | design |
| A2 | assumption | `/kairyn:grill` keeps its name and arguments when it moves from a command to a skill. | design |
| A3 | assumption | Existing evals that follow stage files directly keep passing. | build |
| A4 | assumption | Script-only commands do not need a large model. | design |
| A5 | assumption | Success is a lower measured cost per eval run at the same pass rate, before and after. Build runs only the evals the selector picks, to limit new spend. | Jayson |
| A6 | assumption | Cost comes from `total_cost_usd`, a client-side estimate, not the bill. | design |
| A7 | assumption | `running-stages.md` explains the skills. The plugin version goes up. | build |
| K1 | risk | `model:` lasts one turn. Grill answers and the approval reply run on the session model. | design |
| K2 | risk | A smaller model drops eval quality. Design picks each model from eval evidence. | design |
| K3 | risk | A skill `description` that says what but not when never triggers (backlog `skill-checks`). | design |

## Acceptance criteria
- [ ] `plugin/skills/` has a `SKILL.md` for `requirements`, `grill` and `model-routing`. A test proves it. (R1)
- [ ] Each skill references `.kairyn/stages/<STAGE>.md` and holds no stage steps. A test proves it. (R2)
- [ ] Each skill has a `model:` value, chosen in design with before and after eval cost and pass rate in the task folder. (R3, K2)
- [ ] A skill run with no stage file names `/kairyn:upgrade`. A test proves the text. (R4)
- [ ] The init, check and upgrade commands have `model:`, and their evals pass. (R5)
- [ ] An eval run writes cost per scenario and a total to `summary.md`. A test proves the parser. (R6)
- [ ] The requirements, grill and model-routing evals pass through their skills. (R1, R3)
- [ ] The existing evals pass without the skills. (R7)
- [ ] `claude plugin validate plugin` and `uv run pytest` pass. New markdown files have budgets. (A7)
- [ ] Design states how K1 is handled. (K1)

## Open questions and answers
- Q1: Subagents or skills? A: A skill per stage (user, 2026-11-22). Replaces the generated subagents draft.
- Q2: Where does the cost go? A: Both evals and stage runs. About $400 is already spent; the goal is to cut what new runs cost (user).
- Q3: Which stages? A: The built-in stages; user-added stages keep the file route (Claude, follows from Q1).

Approval: Jayson De los Reyes, 2026-11-22T12:36:15Z, "Approve both"
