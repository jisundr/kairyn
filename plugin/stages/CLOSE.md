---
name: close
order: 90
optional: true
purpose: Turn a done task into an ADR, a changelog entry and learnings, then delete the task. Run it after the task's change merges.
---

# Stage: close

Optional: run it after a task's change merges. `/kairyn:close <task>` runs it. Code is the fact; git history keeps the task folder.

## Inputs
- The task folder: `STATE.md`, `REQUIREMENTS.md` and later stage outputs.
- `docs/adr/`, `CHANGELOG.md` and `.kairyn/learnings.md`, if present.

## Steps
1. Run the close script (the skill names it) with `record-merge <task>` (with `--pr <n>` if the user names a pull request), then `check <task>`. On `FAIL`, report it and stop.
2. Read the task outputs. Find load-bearing decisions: a trade-off, a new dependency, or a break from a pattern. A `D<n>` or `Q<n>` answer is a candidate. Most have none.
3. For each one, get a path from `adr-path <slug>`. Write the ADR there (Nygard form): `# <n>. <title>`, `Date: <date>`, then `## Status` (Accepted), `## Context`, `## Decision`, `## Consequences`. Name the task in Context. Write only what the task outputs state.
4. Append each durable rule the task taught to `.kairyn/learnings.md`: `- <date> [close] <rule>`. Skip rules already there.
5. Write one changelog line: what changed for a user of the repo, at most 25 words.
6. Run `close <task> --entry "<line>"`. Report every line it prints: each `LINK:` is a link to fix, each `UNLINKED:` an idea to delete by hand.
7. On a `RETRO:` line, follow `.kairyn/stages/RETRO.md` in this turn.

## Output
No task output: `close` deletes the folder. The outputs are the ADRs, the `CHANGELOG.md` entry and the learnings. Write them in ASD-STE100 (see `_template.md`, Writing). Get dates from `date +%Y-%m-%d`.

## Exit criteria
- [ ] `close` printed `DELETED docs/tasks/<task>/`.
- [ ] Each ADR has the four sections. No ADR holds a fact the task outputs do not state.

## State update
None: the task folder is gone.

## Learnings
Step 4 writes them.
