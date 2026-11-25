---
title: Harness overview
summary: "How this repo's AI workflows are documented, and how to keep the docs lean."
read_when: "looking for the repo's AI workflows or adding a harness doc"
load: on-demand
---

# .harness

Workflow docs for AI sessions in this repo, set up by `/kairyn:init`. Add your own beside these.

<!-- harness-docs:start -->
| Workflow | Use it when |
|---|---|
| [AFK run](workflows/afk-run.md) | running /kairyn:build or /kairyn:review, or editing afk.yml |
| [Keeping docs lean](workflows/keeping-docs-lean.md) | adding or editing a harness doc, or when /kairyn:check fails |
| [Milestones](workflows/milestones.md) | setting up milestones.yml |
| [Running stages](workflows/running-stages.md) | running a stage, or editing or adding stage instructions |
| [Task lifecycle](workflows/task-lifecycle.md) | starting or resuming a task, or touching STATE.md or task folders |
<!-- harness-docs:end -->

## Principles

1. Read a doc only when the task matches its `read_when`.
2. Script what must always work. Leave the model what needs judgment.
3. Keep files lean: budgets live in `budgets.yml`. Run `/kairyn:check`.
4. After a kairyn update, run `/kairyn:upgrade`. It keeps your edits.
