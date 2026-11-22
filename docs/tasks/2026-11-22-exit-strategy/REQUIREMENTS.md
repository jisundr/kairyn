---
task: 2026-11-22-exit-strategy
stage: requirements
summary: "An exit stage turns a done task into an ADR and a changelog entry, then deletes its folder and backlog files."
---

# Requirements: exit strategy for done tasks

## Problem statement

The request is "implement the exit strategy as well so that we can delete the done task and backlogs as well as creating artifacts". Done task folders and closed backlog files stay in `docs/` forever. They drift from the code, and agents read them as if they were current. Nothing records what shipped in a short, durable form.

## Grounding

- Three tasks have `status: done`: `grill-me`, `plugin-versioning`, `requirements-gaps`.
- `docs/backlog/` has `committed` and `dropped` files. A committed file links its task in the Log.
- The repo has no `CHANGELOG.md`, no `docs/adr/` and no git tags. Releases are version bumps in `plugin.json`.
- Knowledge-base `Spec Exit Strategy`: verify, record ADRs, promote durable rules, apply retention. Git history keeps deleted files.

## Scope

In:
- An optional `exit` stage and a `/kairyn:exit <task>` entry point. (request, A1)
- An ADR in `docs/adr/` for each load-bearing decision of the task. (request)
- A `CHANGELOG.md` entry per task, under `## Unreleased`. (request)
- Deletion of the task folder and its closed backlog files. (request, A3)
- A release tag whose notes are the changelog section. (request, A5)
- Docs, budgets, tests, an eval and a version bump that the repo rules require. (A7)

Out:
- Frozen task folders or a task index. The user chose a changelog (Q1).
- A published summary page. The release tag replaces it (Q2).
- Pushing tags or creating GitHub releases without the user's go-ahead.

## Requirements
- R1: When the user runs exit on a task with `status: done` and an approval line, kairyn shall write its artifacts, then delete the task. (request)
- R2: If the task is not `done` or has `Approval: pending`, exit shall stop and change nothing. (A2)
- R3: When a task has a load-bearing decision, exit shall write `docs/adr/<NNNN>-<slug>.md` in Nygard form. (request, A4)
- R4: Exit shall add one entry for the task under `## Unreleased` in `CHANGELOG.md`, and create the file if it is missing. (request)
- R5: Exit shall delete `docs/tasks/<task>/` and each backlog file whose Log links the task. (request, A3)
- R6: When a backlog index row links a deleted file, exit shall remove the row. (A6)
- R7: When the user cuts a release with a version, kairyn shall move `## Unreleased` to `## <version>` and create a local annotated tag `v<version>` with that section as its message. (request, A5)
- R8: Exit shall append durable rules from the task to `.kairyn/learnings.md` before it deletes the task. (A8)

## Non-functional needs
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states one.
- Security: not applicable: deletion stays inside `docs/` and is reversible from git (R5).
- Observability: exit prints each file it writes and deletes (A1).

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | A script in `plugin/scripts/` does the checks, changelog, deletion and tag. The model writes only the ADR and the entry text. | design |
| A2 | assumption | Only `status: done` with an approval line counts as done. | Jayson |
| A3 | assumption | `dropped` backlog files with no task are deleted too. `parked` and open files stay. | Jayson |
| A4 | assumption | A decision is load-bearing if it is a trade-off, a new dependency or a break from a pattern. Else no ADR. | design |
| A5 | assumption | The user gives the version. In this repo it is the `plugin.json` version. | design |
| A6 | assumption | The backlog index is `docs/backlog/README.md` when it exists. | design |
| A7 | assumption | `task-lifecycle.md` and `running-stages.md` describe exit. The plugin version goes up. | build |
| A8 | assumption | Learnings stay in `.kairyn/learnings.md`, the native home for stage rules. | design |
| K1 | risk | Exit deletes a task that has not merged. The branch still holds it. | design |
| K2 | risk | Links in other docs point at deleted tasks. Exit reports them. | design |
| D1 | dependency | Task `2026-11-22-stage-skills` makes stages skills. `/kairyn:exit` follows its form. | design |

## Acceptance criteria
- [ ] A test runs exit on a done, approved fixture task and gets an ADR, a changelog entry, a learning and no task folder. (R1, R3, R4, R8)
- [ ] A test runs exit on a blocked task and on a pending approval, and nothing changes. (R2)
- [ ] A test proves no ADR is written for a task with no load-bearing decision. (R3)
- [ ] A test proves linked `committed` and `dropped` backlog files are deleted and `parked` files stay. (R5)
- [ ] A test proves index rows for deleted files are removed. (R6)
- [ ] A test proves the release step moves `## Unreleased` and creates tag `v<version>` with that text. It pushes nothing. (R7)
- [ ] An eval runs `/kairyn:exit` on a fixture task and passes the checks above. It fails before the stage exists. (R1)
- [ ] Exit runs on this repo's three done tasks. The pull request shows the ADRs and changelog. (R1)
- [ ] `claude plugin validate plugin` and `uv run pytest` pass. New markdown files have budgets. (A7)

## Open questions and answers
- Q1: Delete, or freeze and index? A: Delete, and keep a changelog (user).
- Q2: Which artifacts? A: ADRs, a changelog entry, and a release tag instead of a published page (user).

Approval: pending
