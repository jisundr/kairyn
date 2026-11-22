# 2. Grilling is an optional stage, not a requirements step

Date: 2026-11-22

## Status
Accepted

## Context
Task 2026-11-22-grill-me added an interview that runs before a spec exists. The agent asks one hard question at a time until the user and the agent share one concept. Four places were possible: a step in `requirements`, an optional stage, a command alone, or backlog shaping. A step in `requirements` makes small tasks long, and that stage has a 500-token budget. A command alone keeps no task state. No backlog stage exists.

## Decision
Grilling is the optional `grill` stage (`GRILL.md`), run by `/kairyn:grill`. It writes `CONCEPT.md` in the task folder. When `CONCEPT.md` exists, `requirements` takes its decisions as answers. Grill ends by naming the task folder, and the user runs requirements on that folder.

## Consequences
- Small tasks skip grilling. The user must ask for it.
- Grill creates the task folder and `STATE.md` when they do not exist.
- A later backlog stage can run the same stage in its shaping step.
