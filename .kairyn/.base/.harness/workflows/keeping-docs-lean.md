---
title: Keeping docs lean
summary: "The doc header format, load classes, size budgets and the /kairyn:check command."
read_when: "adding or editing a harness doc, or when /kairyn:check fails"
load: on-demand
---

# Keeping docs lean

Every doc in `.harness/` starts with a header an AI can read without opening the body (`head -6 <file>`):

```yaml
---
title: <name>
summary: "<one line, at most 160 characters>"
read_when: "<the task that makes this doc relevant>"
load: on-demand
---
```

`load` says when a file is read: `always` (every session), `on-demand` (when `read_when` matches) or `runtime` (when a command or stage runs).

Size limits per file pattern are in `.harness/budgets.yml` (estimated tokens, characters / 4). Files that kairyn installs also have built-in limits, checked after your patterns, so your own limit wins.

## Commands

- `/kairyn:check` verifies headers, index tables and budgets.
- `/kairyn:check write` also regenerates the index tables in `CLAUDE.md` and `.harness/README.md`.

After adding a doc, give it a header, run `/kairyn:check write`, and fix anything over budget by cutting, not by raising the limit.
