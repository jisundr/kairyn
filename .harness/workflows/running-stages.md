---
title: Running stages
summary: "How to run a kairyn stage, where its instructions live, and what it leaves behind."
read_when: "running a stage, or editing or adding stage instructions"
load: on-demand
---

# Running stages

Stage instructions are in `.kairyn/stages/`, one file per stage, in `order`. They belong to this repo: edit them freely. `/kairyn:init` never overwrites them.

## Run one

Ask Claude to follow `.kairyn/stages/<STAGE>.md` for your request, for example: "Follow `.kairyn/stages/REQUIREMENTS.md` for: add a dry-run flag."

A stage:
1. reads `STATE.md` and earlier stage outputs (see `task-lifecycle.md`)
2. writes its output to `docs/tasks/<date>-<slug>/<STAGE>.md`
3. updates `STATE.md` and appends to `.kairyn/learnings.md`

## Add a stage

Copy `.kairyn/stages/_template.md`, give it the next `order`, and list it under `stages:` in `.kairyn/templates/STATE.md`. Required sections: Inputs, Steps, Output, Exit criteria, State update, Learnings.
