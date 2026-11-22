---
task: 2026-11-22-stage-agents
stage: requirements
summary: "Generate a Claude Code subagent for every stage in .kairyn/stages/, each with its own model, and never overwrite user edits."
---

# Requirements: generated stage agents with a model per agent

## Problem statement

The request is "setup model routing and agents". Today every stage runs in the user's main session, on the session model. kairyn ships no subagents. The user chose generated agents: a script writes one subagent file per stage in `.kairyn/stages/`, built-in or user-added. Each subagent names the Claude model it runs on.

## Grounding

- `plugin/` has no `agents/`. Stages run when the user asks Claude to follow `.kairyn/stages/<STAGE>.md` (`running-stages.md`).
- Stages today: `requirements` and the optional `model-routing`. Users can add stages from `_template.md`.
- Stage front matter has `name`, `order`, `purpose`, and `optional` for some stages. It has no `model` key.
- `plugin/hooks/hooks.json` runs `version_check.py` at SessionStart. `kairyn_files.py` records installed files and their hashes.
- kairyn makes no LLM API calls. The only model settings are the session model and `KAIRYN_MODEL` in `evals/runner.py`.

## Scope

In:
- A script in `plugin/scripts/` that writes `.claude/agents/kairyn-<name>.md` for each stage file. (request)
- A `model:` value in each generated agent. (request)
- An optional `model` key in stage front matter, the source of the agent's model. (A3)
- Generation without a manual step: at `/kairyn:init` and at SessionStart. (request, A5)
- Docs, budgets and a version bump that the repo rules require. (A7, A8)

Out:
- Fixed agent files shipped in `plugin/agents/`.
- Agents for stages that do not exist yet (design, build, `idea-triager`). They get one when their stage file exists.
- Deleting the agent of a removed stage. The script reports it only.
- Runtime routing from the MODEL-ROUTING stage (logging, failover, cache, router). kairyn has no LLM call sites.
- A change to `KAIRYN_MODEL` or to how evals pick a model.

## Assumptions

- A1: The script skips `_template.md` and files without a `name` in front matter.
- A2: Each agent tells Claude to follow `.kairyn/stages/<STAGE>.md` at run time. It does not copy the stage steps. A stage edit takes effect with no new generation.
- A3: The agent's `model` comes from the stage's `model` key. If the stage has no `model` key, the agent gets `model: inherit`.
- A4: The `model` values for the built-in stages are a design decision. Design compares models on the stage evals, and the user approves the values.
- A5: Agent name, description and model change only when the script runs again. Claude Code loads agents at session start, so a new agent from the SessionStart run appears in the next session or after `/agents`. Design confirms this.
- A6: The script never overwrites an agent file that the user edited or wrote. It records each file it writes, as `kairyn_files.py` does, and replaces only unedited files.
- A7: Each new markdown file gets a budget in `.harness/budgets.yml`. `running-stages.md` explains the agents.
- A8: A plugin change raises the plugin version, as `upgrade.md` requires.
- A9: Running a stage without its agent, as today, keeps working.
- A10: The agents playbook allows a separate agent only for isolated context, different permissions, or parallel work. A model per stage is not one of these reasons.

## Acceptance criteria

- [ ] The script writes one `.claude/agents/kairyn-<name>.md` per stage file and skips `_template.md`. A test proves it with a user-added stage. (request, A1)
- [ ] Each agent has front matter with `name`, `description` (from the stage `purpose`) and `model`. (request)
- [ ] A stage with `model: haiku` gives an agent with `model: haiku`. A stage with no `model` gives `model: inherit`. Tests prove both. (A3)
- [ ] The built-in stages have the `model` values the user approved in design, with eval evidence in the task folder. (A4)
- [ ] Each agent tells Claude to follow `.kairyn/stages/<STAGE>.md` and copies no stage steps. (A2)
- [ ] A second run with no change writes nothing. A run after a stage `model` change updates that agent. (A5, A6)
- [ ] A run keeps an agent file the user edited or wrote, and reports it. Tests prove both cases. (A6)
- [ ] A run reports an agent whose stage file no longer exists and does not delete it. (request)
- [ ] `/kairyn:init` and the SessionStart hook run the script. The hook stays within its timeout and never fails the session. (request, A5)
- [ ] An eval runs the `requirements` stage through its generated agent and passes the stage's existing checks. It fails before the script exists. (request, A2)
- [ ] Following a stage file in the main session, without an agent, still passes the existing evals. (A9)
- [ ] `claude plugin validate plugin` and `uv run pytest` pass. Every new markdown file is under a budget in `.harness/budgets.yml`. (A7)
- [ ] Design names which A10 reason each stage agent meets, or replaces agents with skills. (A10)
- [ ] `running-stages.md` explains the agents and the stage `model` key in the same commit. The plugin version goes up. (A7, A8)

## Open questions and answers

- Q1: Which meaning of "model routing and agents"? A: Stage agents, each with a model (user).
- Q2: Fixed agent files or agents made on the fly? A: Generated files, one per stage, built-in or user-added (user).
- Q3: Which stages get agents? A: Every stage file in `.kairyn/stages/` (user, follows from Q2).
- Q4: Run the MODEL-ROUTING stage on this task? A: No. kairyn makes no LLM API calls (user).
- Q5: Which A10 reason justifies stage agents? A: Open. Design answers it (playbook update, 2026-11-22).
