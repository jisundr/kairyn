# 5. Delete done tasks and keep a changelog

Date: 2026-11-23

## Status
Accepted

## Context
Task 2026-11-22-exit-strategy. Done task folders and closed backlog files stayed in `docs/` forever. They drifted from the code, and agents read them as if they were current. Nothing recorded what shipped in a short, durable form. Two options were possible: freeze done tasks and index them, or delete them.

## Decision
Delete them (Q1). An optional `exit` stage, `/kairyn:exit <task>`, writes an ADR in `docs/adr/` for each load-bearing decision, one line under `## Unreleased` in `CHANGELOG.md` and learnings. Then `exit.py` deletes the task folder, its `committed` backlog files and `dropped` backlog files with no task, and their index rows. `parked` and open backlog files stay. A release tag holds the changelog section instead of a published page (Q2).

## Consequences
- Git history is the only copy of a closed task's outputs.
- A script does the checks, deletion, changelog and tag. The model writes only the ADR and the entry text.
- `exit.py release` tags locally and never pushes.
- Links in other docs to a deleted task break. `close` reports them.
