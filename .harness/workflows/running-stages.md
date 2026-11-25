---
title: Running stages
summary: "How to run a kairyn stage, where its instructions live, and what it leaves behind."
read_when: "running a stage, or editing or adding stage instructions"
load: on-demand
---

# Running stages

Stage instructions are in `.kairyn/stages/`, one file per stage, in `order`. They belong to this repo: edit them freely. `/kairyn:init` never overwrites them.

## Run one

Run its skill: `/kairyn:requirements add a dry-run flag`, `/kairyn:design <task folder>`, `/kairyn:grill <topic>` or `/kairyn:model-routing <task folder>`. Or ask Claude to follow `.kairyn/stages/<STAGE>.md` for your request. That route works for stages you add.

Each skill names a cheaper model in its `model:` front matter. The model applies to the turn the skill runs. Your next reply, for example an approval or a grill answer, runs on the session model. Set a cheaper session model with `/model` for long stages.

A stage:
1. reads `STATE.md` and earlier stage outputs (see `task-lifecycle.md`)
2. writes its output to `docs/tasks/<date>-<slug>/<STAGE>.md`
3. updates `STATE.md` and appends to `.kairyn/learnings.md` (this repo's `.gitattributes` merges it by `union`, so parallel task branches do not conflict on a local merge or rebase)

An optional stage (`optional: true` in its front matter) is not in the default stage list. Run it on a task only when it fits: `GRILL.md` before `requirements` when a request is vague, `MODEL-ROUTING.md` after it to cut model cost, `CLOSE.md` (`/kairyn:close`) after a task merges, `RETRO.md` (`/kairyn:retro`) when `learnings.md` is past half its budget. It adds itself to the task's `stages`.

## Approve requirements and design

`requirements` and `design` end with `status: blocked` and `Approval: pending` in their output. Read it, then approve in chat. Claude writes `Approval: <your git name>, <timestamp>, "<your words>"` and moves the task on: requirements to `design`, design to `build`. A reply that does not approve changes nothing. To design another way, name an option from `DESIGN.md`: Claude rewrites it. The sections are in `.kairyn/templates/`.

## The AFK run: build, gates, review

`/kairyn:build <task>` runs them with no user turns, after design approval. See `afk-run.md`.

## Add a stage

Copy `.kairyn/stages/_template.md`, give it the next `order`, and list it under `stages:` in `.kairyn/templates/STATE.md`. Required sections: Inputs, Steps, Output, Exit criteria, State update, Learnings.
