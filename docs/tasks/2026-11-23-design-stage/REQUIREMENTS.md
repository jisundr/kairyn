---
task: 2026-11-23-design-stage
stage: requirements
summary: "Requirements for a required design stage: /kairyn:design on Opus writes DESIGN.md, waits for approval, and has a two-scenario eval."
---

# Requirements: Design stage between requirements and code

## Problem statement
After requirements, kairyn gives no help to choose an approach or split work into tasks. Agents code from the spec and guess the plan. Requirements is the only stage, so a task is `done` before any design or code exists.

## Scope
In: a required `design` stage, its skill, its output `DESIGN.md` and its eval (D1, D4).
In: the requirements stage hands every task to design (D4).
Out: a build stage. The standards impact section (D5). Automatic handoff between stages (backlog idea `approval-handoff`). Two approval stops (D3). Sonnet for design (D6). Changes to `exit.py`.

## Requirements
- R1: The kairyn plugin shall ship a required stage `plugin/stages/DESIGN.md` and a skill `/kairyn:design` that runs it. (D1, D2, D4)
- R2: The design skill shall run on `model: opus`. (D6)
- R3: When the user approves requirements, the requirements stage shall set `stage: design` and keep `status: in-progress`. (D4)
- R4: The `STATE.md` template shall list `design: pending` after `requirements` under `stages`. (D4)
- R5: When the design stage runs, it shall read `STATE.md`, `REQUIREMENTS.md`, `CONCEPT.md` if present, `.kairyn/learnings.md` and the code that the criteria touch. (D1, request)
- R6: If `REQUIREMENTS.md` has no approval line, the design stage shall write nothing and tell the user to approve requirements first. (D1)
- R7: The design stage shall write `DESIGN.md` with the output front matter and four sections: Approach, Options, Tasks, Test plan. (D5)
- R8: The Options section shall list at least two options with cost and risk, and one option shall be the smallest thing. (D5, D7)
- R9: The Tasks section shall list tasks in dependency order, each with a done condition. (D5)
- R10: The Test plan shall map each acceptance criterion in `REQUIREMENTS.md` to a task and a test. (D5)
- R11: Where `DESIGN.md` names a file path, the path shall exist in the repo or carry the mark `(new)`. (D7, A2)
- R12: When it writes `DESIGN.md`, the design stage shall end it with `Approval: pending`, set `design: done` and `status: blocked`, and ask for approval. (D3)
- R13: If a reply neither approves nor names an option, the design stage shall change nothing. (D3)
- R14: When the user names another option, the design stage shall rewrite `DESIGN.md` for that option and keep `Approval: pending`. (D3)
- R15: When the user approves, the design stage shall write the approval line in the requirements format and set `status: done`. (D3, D4)
- R16: The eval `evals/promptfoo/design.yaml` shall run scenario 1 on a fixture task with approved requirements. It checks well_formed, traceable, options, grounded and waits_for_approval, and a judge scores no_invention and plan quality. (D7)
- R17: The design eval shall run scenario 2: a reply that does not approve, then "go with option B", then an approval. (D7)
- R18: The design eval shall gate at a 0.9 pass rate over 10 runs and a judge mean of 4. (D7)
- R19: The requirements eval shall expect `stage: design` and `status: in-progress` after approval. (D7)
- R20: The harness docs and the README shall describe the design stage in the same change. (A3)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a time limit.
- Security: not applicable: the stage reads repo files only.
- Observability: not applicable: eval summaries already show cost per run.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | The design stage has `order: 2`, and its template is `plugin/templates/DESIGN.md`. | build |
| A2 | assumption | `DESIGN.md` marks each file it creates `(new)`, so `grounded` skips it. | Jayson |
| A3 | assumption | CLAUDE.md rule: a workflow change updates its `.harness` doc in the same commit. | build |
| A4 | assumption | `/kairyn:upgrade` installs the new stage, skill and template in existing repos with no script change. | build |
| A5 | assumption | Tasks already `done` after requirements stay as they are. | Jayson |
| K1 | risk | `REQUIREMENTS.md` (stage) is at 498/500 tokens. The R3 change must cut words elsewhere. | build |
| K2 | risk | Two Opus scenarios at 10 runs cost many tokens per release. | Jayson |

## Acceptance criteria
- [ ] `claude plugin validate plugin` passes, and `tests/test_static.py` and `tests/test_skills.py` accept the design stage and skill. (R1, R2)
- [ ] The requirements eval passes with `stage: design` after approval. (R3, R19)
- [ ] A test reads `plugin/templates/STATE.md` and finds `design: pending` after `requirements`. (R4)
- [ ] Design scenario 1 passes well_formed, traceable, options, grounded and waits_for_approval at 0.9 over 10 runs, with judge mean 4. (R5, R7, R8, R9, R10, R11, R12, R16, R18)
- [ ] Design scenario 2 passes at 0.9 over 10 runs. The first reply changes nothing, option B gets a rewrite, and approval sets `status: done`. (R13, R14, R15, R17, R18)
- [ ] A reviewer finds the approval check in the first step of `plugin/stages/DESIGN.md`. (R6)
- [ ] `uv run pytest` passes, and `running-stages.md` and the README name the design stage. (R20)

## Open questions and answers
None. `CONCEPT.md` D1 to D7 answer the design questions.

Approval: Jayson De los Reyes, 2026-11-23T01:07:13Z, "approved"
