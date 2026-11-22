---
task: 2026-11-22-requirements-gaps
stage: requirements
summary: "The requirements stage writes EARS requirements, non-functional needs and owned risks, and waits for human approval."
---

# Requirements: close the playbook gaps in the requirements stage

## Problem statement

The request is "Let's create task for this" on two backlog items: `grill-requirements` and `requirements-gaps`. Pull request #17 shipped grilling as the optional `grill` stage, so this task covers only the playbook gaps. The requirements output has no EARS requirements, no non-functional needs, no risks with owners and no approval line. So a later stage can build from a spec that nobody approved.

## Grounding

- `plugin/stages/REQUIREMENTS.md` writes acceptance criteria and ends at exit criteria. It reads `CONCEPT.md` from `grill` and accepts `(D1)` as a source.
- `plugin/stages/REQUIREMENTS.md` is at 496/500 tokens. `_template.md` is at 489/500. `GRILL.md` is at 498/500. The `plugin/stages/*.md` budget is 500.
- `evals/checks.py` `structural_problems` fails a run when `stage` is `requirements` and `status` is not `done`.
- The grill eval drives scripted turns through `evals/runner.py`. A conversation eval for approval can reuse it.
- Playbook `knowledge-base/03 Playbooks/SDLC/01 Handling New Requirements.md`: steps 5, 7, 8 and 9, the EARS cheat sheet and gates 1 to 4.
- The `2026-11-22-stage-agents` task waits on approval by hand: `status: blocked` and a log line.

## Scope

In:
- EARS requirements, each mapped to at least one acceptance criterion. (request)
- Non-functional needs: accessibility, performance, security, observability. (request)
- Assumptions, risks and dependencies, each with an owner. (request)
- An approval line that the agent writes only after the user approves in chat. (request)
- Eval and test changes for the new behavior. Docs, budgets and a version bump that the repo rules require. (A5, A6)

Out:
- Grilling in the requirements stage. The `grill` stage does it.
- A change to `GRILL.md`, for example questions in rounds. Backlog item `grill-rounds` holds it.
- A script or command that writes the approval line.
- Approval gates in stages that do not exist yet (design, build).
- Changes to tasks that already exist, for example `2026-11-22-stage-agents`.

## Assumptions

- A1: The stage file stays within 500 tokens. Design cuts or splits text. The budget does not go up.
- A2: Each EARS requirement has an ID (`R1`, `R2`). Each acceptance criterion names the requirement it checks.
- A3: Until the user approves, the stage ends with `stages.requirements: done`, `status: blocked` and `Approval: Jayson, 2026-11-22T11:16:26Z, "Approve"`. The eval check changes to accept this.
- A4: The approval line holds the approver's name, a UTC timestamp from `date` and the user's words. After approval the agent sets `status: done`.
- A5: A conversation eval proves the approval, with the turn runner from the grill eval.
- A6: The change to `plugin/` raises the plugin version, as `upgrade.md` requires. `running-stages.md` explains the approval.
- A7: A non-functional need that does not apply is written `not applicable: <reason>`.

## Risks and dependencies

| ID | Risk or dependency | Owner |
|---|---|---|
| K1 | All four additions do not fit in 500 tokens. | design stage |
| K2 | The agent writes the approval line from words that do not approve. | design stage |
| K3 | EARS "shall" reads as a modal verb next to the ASD-STE100 rules. | design stage |
| D1 | The consumer fixture and the upgrade test change with the stage file. | build |

## Acceptance criteria

- [ ] `REQUIREMENTS.md` has a Requirements section in EARS form, IDs per A2. Each requirement maps to at least one acceptance criterion. An eval check proves it. (request, A2)
- [ ] `REQUIREMENTS.md` states each of the four non-functional needs, or marks it per A7. An eval check proves it. (request, A7)
- [ ] Each assumption, risk and dependency has an owner. An eval check proves it. (request)
- [ ] With no approval, the run ends per A3 and the requirements eval passes. (request, A3)
- [ ] After the user approves in chat, the approval line matches A4 and `status` is `done`. A conversation eval proves it. (request, A4, A5)
- [ ] The agent never writes the approval line without the user's approval. An eval proves it. (request)
- [ ] A run that starts from a `grill` task folder still passes the existing requirements eval. (request)
- [ ] `plugin/stages/REQUIREMENTS.md` and `_template.md` stay within budget. `uv run pytest` and `claude plugin validate plugin` pass. (A1)
- [ ] Each new eval check fails before its stage change. (A5)
- [ ] `running-stages.md` and `task-lifecycle.md` change in the same commit. The plugin version goes up. (A6)

## Open questions and answers

- Q1: Where does grilling live? A: In the optional `grill` stage, as shipped. The requirements stage does not grill (user, revised after #17).
- Q2: One question at a time or in rounds? A: Out of scope here. Backlog item `grill-rounds` moves `grill` to rounds (user, revised after Matt Pocock's `grilling` skill).
- Q3: How does a human approve? A: The agent records the approval line after the user approves in chat (user).
- Q4: Which playbook gaps are in scope? A: All four: approval, EARS, non-functional needs, risks with owners (user).

Approval: Jayson, 2026-11-22T11:16:26Z, "Approve"
