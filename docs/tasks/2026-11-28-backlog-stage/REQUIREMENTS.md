---
task: 2026-11-28-backlog-stage
stage: requirements
summary: "Ship a backlog stage: /kairyn:idea captures an idea, /kairyn:triage records owner decisions, and a commit starts a task."
---

# Requirements: Backlog stage

## Problem statement
As D1 in `CONCEPT.md`: ideas are handled by hand from rules only this repo has (`TRIAGE.md`). Plugin users get no rules, and requirements does not start from a committed idea. Done when a user repo carries an idea to requirements with shipped steps, each decision logged with who made it. (D1)

## Scope
In: an optional `backlog` stage, `BACKLOG.md`, with the rules. (D3, D4)
In: `/kairyn:idea <request>` to capture one idea. (D3)
In: `/kairyn:triage` for the digest, keep, park or drop, prune and commit. (D2, D3)
In: grill and requirements read the idea that a task's `STATE.md` links. (D5)
In: this repo's `TRIAGE.md` keeps only its Next and Parked notes. (D4)
Out: a shape or pitch step; grill does the shaping. (D2)
Out: deduplication and clustering of ideas. (A5)
Out: changes to init and to the `/kairyn:backlog` page. (D3, D4)

## Requirements
- R1: The plugin shall ship `plugin/stages/BACKLOG.md` as an optional stage that holds the idea file rules: name, front matter, statuses, effort and impact levels, log lines and who decides. (D3, D4)
- R2: When the user runs `/kairyn:idea <request>`, the idea skill shall write one file `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md`, named from the UTC time that `date` gives. (D3)
- R3: The idea file shall hold `title`, `status: inbox`, `requester`, `date`, proposed `effort` and `impact`, the request word for word, a problem marked as an AI draft, and a `[capture]` log line that says the AI proposed effort and impact. (D5, A1)
- R4: If `docs/backlog/` or `docs/backlog/README.md` is missing at capture, the capture script shall create it, with a table that has the columns Idea, Effort, Impact and Notes. (D4)
- R5: The capture script shall never overwrite an existing idea file or `README.md`. (A2)
- R6: When the user runs `/kairyn:triage`, the triage skill shall list each `inbox` idea and each `parked` idea whose `review_by` is before today, each with a proposed keep, park or drop and one reason. (D2)
- R7: The triage skill shall change an idea only after the owner decides it in chat. (D2)
- R8: When the owner keeps, parks, renews or drops an idea, the triage script shall set its `status` (`triaged`, `parked` or `dropped`) and append a `[triage]` log line with the timestamp, the decision and the owner's name. (D2)
- R9: When the owner parks or renews an idea, the triage script shall set `review_by` to the date the owner gives. (D2, A3)
- R10: When the owner keeps an idea, the triage script shall log the confirmed effort and impact and add the idea's README row. (D2, A4)
- R11: When the owner parks or drops an idea, the triage script shall remove its README row, if present. (A4)
- R12: When the owner commits a `triaged` idea, the commit script shall set `status: committed`, append a `[commit]` log line with the owner's name, and create `docs/tasks/<YYYY-MM-DD>-<idea slug>/STATE.md` that links the idea file. (D5, A6)
- R13: After a commit, the commit script shall print the commands `/kairyn:grill <task folder>` and `/kairyn:requirements <task folder>`. (D5)
- R14: If the task folder already exists, or the idea is not `triaged`, the commit script shall change no file and exit with an error line. (A2, A6)
- R15: When grill or requirements runs on a task folder whose `STATE.md` links an idea file, the stage shall take that idea's raw request and problem as the request. (D5)
- R16: This repo's `docs/backlog/TRIAGE.md` shall keep only its Next and Parked sections and point to `BACKLOG.md` for the rules. (D4)

## Non-functional needs
- Accessibility, performance, security: not applicable: no source states a need.
- Observability: each decision is a log line with who made it. (D1)
- Size: `BACKLOG.md` stays within 500 tokens and each skill within 300 tokens (`.harness/budgets.yml`). (A7)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | `requester` is `git config user.name` unless the request names another person. | owner |
| A2 | assumption | Like init, a backlog script never overwrites a user's file. | owner |
| A3 | assumption | A park with no date from the owner gets no default; triage asks for one. | owner |
| A4 | assumption | The README table lists only `triaged` ideas, as in this repo today. | owner |
| A5 | assumption | Dedupe is out: the concept leaves it out. | owner |
| A6 | assumption | Only a `triaged` idea can be committed. | owner |
| A7 | assumption | Scripts in `plugin/scripts/` do the file writes; stage text only decides. | design |
| K1 | risk | GRILL.md and REQUIREMENTS.md are near their budget; R15 needs cuts. | design |
| K2 | risk | Stage text changes need new and re-run evals (backlog, grill, requirements), which cost tokens. | owner |

## Acceptance criteria
- [ ] `plugin/stages/BACKLOG.md` exists, passes `tests/test_static.py` as an optional stage and holds the rules. (R1)
- [ ] Capture script tests: one new idea file with the R3 fields; a missing folder and README are created; an existing file stays unchanged. (R2, R3, R4, R5)
- [ ] An eval of `/kairyn:triage` shows inbox and stale parked ideas, each with a proposal and reason, and no file changed before the owner answers. (R6, R7)
- [ ] Triage script tests: each decision sets `status`, `review_by`, the owner's log line and the README row. (R8, R9, R10, R11)
- [ ] Commit script tests: the status, log line, `STATE.md` link and two commands; an existing folder or untriaged idea changes nothing. (R12, R13, R14)
- [ ] Grill and requirements evals, started on a committed task folder, take the idea's request and problem. (R15)
- [ ] `TRIAGE.md` has only Next, Parked and a `BACKLOG.md` pointer. (R16)

## Open questions and answers
- Q1: Confirm A1, A3, A4, A6? A: pending (owner)

Approval: pending
