# 6. Design is a required stage with one approval stop

Date: 2026-11-23

## Status
Accepted

## Context
Task 2026-11-23-design-stage. After requirements, kairyn gave no help to choose an approach or split work into tasks. Agents coded from the spec and guessed the plan. Requirements was the only stage, so a task was `done` before any design or code existed. Two fixes were possible: a real planning stage, or only a later `done` mark (D1). The playbook has two human decisions in design: choose the approach, then approve the plan.

## Decision
- `design` is a required SDLC stage after requirements, not an optional stage like grill (D4). Requirements always sets `stage: design`.
- The name is `design`, not `plan`: the stage chooses an approach, and `plan` collides with Claude Code plan mode (D2).
- The stage stops once. It writes the full `DESIGN.md` for its recommended option. The user approves in chat, or names another option and the stage rewrites the file (D3).
- `DESIGN.md` has four sections: Approach, Options, Tasks, Test plan. Standards impact waits for a gates stage (D5).
- The skill runs on Opus (D6). The eval gates as for requirements, and adds a `grounded` check: each named path exists or carries `(new)` (D7).

## Consequences
- A task is `done` only after design approval. When a build stage exists, design hands the task to it.
- One approval stop keeps the eval like requirements: one `blocked` state and the same approval line check.
- A rejected recommendation costs one rewrite of `DESIGN.md`.
- A move to Sonnet needs a 10-run eval pass first.
