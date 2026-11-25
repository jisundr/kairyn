# 4. Stage skills with a model per stage

Date: 2026-11-23

## Status
Accepted. Amended by 0019: requirements on Sonnet, close and retro on Haiku.

## Context
Task 2026-11-22-stage-skills. Every stage and every eval ran on the session model, and no run recorded its cost. About $400 was already spent. Two options were possible: a subagent per stage, or a skill per stage. The agents playbook says a model per stage is not a reason for a subagent.

## Decision
A skill per built-in stage in `plugin/skills/<stage>/SKILL.md`, with a `model:` key (Q1). Each skill tells Claude to follow `.kairyn/stages/<STAGE>.md` and copies no stage steps. Each model comes from eval evidence: `grill` and `model-routing` on Sonnet, `requirements` on Opus because it failed the 10-run gate on Sonnet. The init, check and upgrade commands run on Haiku. Each eval run writes its cost to `summary.md`.

## Consequences
- In smoke runs, Sonnet skills cost 53 to 59% less per stage run.
- `model:` applies to the skill's turn only. Later turns, such as grill answers and the approval reply, run on the session model.
- User-added stages have no skill and keep the stage-file route.
- A stage edit takes effect with no change to its skill.
- A skill that another skill starts runs on the caller's model, not on its own `model:` (spike, 2026-11-25: `claude -p` 2.1.331; a Sonnet skill that called an Opus skill through the Skill tool ran both on Sonnet; the same skill typed by the user ran on Opus). So an approved stage names the next command for the user to type and never starts the next skill (`_approval.md`).
