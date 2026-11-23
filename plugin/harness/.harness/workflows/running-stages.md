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
3. updates `STATE.md` and appends to `.kairyn/learnings.md`

An optional stage (`optional: true` in its front matter) is not in the default stage list. Run it on a task only when it fits: `GRILL.md` before `requirements` when a request is vague, `MODEL-ROUTING.md` after it to cut model cost, `EXIT.md` (`/kairyn:exit`) after a task merges, `RETRO.md` (`/kairyn:retro`) when `learnings.md` is past half its budget. It adds itself to the task's `stages`.

## Approve requirements and design

`requirements` and `design` end with `status: blocked` and `Approval: pending` in their output. Read it, then approve in chat. Claude writes `Approval: <your git name>, <timestamp>, "<your words>"` and moves the task on: requirements to `design`, design to `build`. A reply that does not approve changes nothing. To design another way, name an option from `DESIGN.md`: Claude rewrites it. The sections are in `.kairyn/templates/`.

## The AFK run: build, gates, review

`/kairyn:build <task>` runs `afk.py` in a worktree with no user turns. For each slice `T<n>`, a fresh `claude -p` follows `BUILD.md`: a `test(T<n>)` commit, then a `feat(T<n>)` commit. The script needs the done command to fail at the first and pass at the second. A read-only reviewer session then reads the diff and the flags (an edited test, an added lint suppression). Its findings get one fix round; if they stay, the run blocks. It then runs the `gates:` in `.kairyn/afk.yml`, and a `REVIEW.md` session. Before the first stage it needs a `testing` gate command, every set gate green on the base commit, and no uncommitted code changes. `limits:` in `afk.yml` caps cost per stage and per run, and minutes per stage. A failed check or a limit sets `status: blocked` with the reason. Run `/kairyn:build` again to resume. The run stops once for you: read the diff and `REVIEW.md`, then `/kairyn:review <task> approve "<words>"` or `reject "<reason>"`.

## Add a stage

Copy `.kairyn/stages/_template.md`, give it the next `order`, and list it under `stages:` in `.kairyn/templates/STATE.md`. Required sections: Inputs, Steps, Output, Exit criteria, State update, Learnings.
