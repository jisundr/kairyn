---
task: 2026-11-28-backlog-stage
stage: design
summary: "One script, backlog.py (capture, digest, decide, commit), an optional BACKLOG.md stage and two skills, /kairyn:idea and /kairyn:triage."
---

# Design: Backlog stage

## Approach
Option A. A script does every file write (A7), so status, log lines, README rows and the task folder are the same every time. The stage text only drafts and proposes; the owner decides (R7). Each stage file stays in budget (K1).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `plugin/scripts/backlog.py` with `capture`, `digest`, `decide` and `commit`; `BACKLOG.md`; skills `idea` and `triage` (Sonnet). | 1 script, 1 stage, 2 skills, 4 evals. | `BACKLOG.md` holds rules and steps in 500 tokens. |
| B | Stage text only: the model writes files from the rules. | No script. | Breaks "script what must always work"; log lines and README rows drift. |
| C | Grow `backlog_html.py` with write subcommands. | 1 file less. | A view-only page script starts to write ideas (ADR 0018). |

## Tasks
- T1: Capture, tracer bullet. `backlog.py capture --slug --title --effort --impact --request --problem` writes the idea file with `status: inbox`, `requester` from `git config user.name` (A1), a `[capture]` line; creates `docs/backlog/README.md` with the four-column table if missing; refuses an existing file. `BACKLOG.md` gets the rules and capture steps; skill `idea` runs them. Eval `idea` (scenario `idea_capture`). Files: `plugin/scripts/backlog.py` (new), `plugin/stages/BACKLOG.md` (new), `plugin/skills/idea/SKILL.md` (new), `tests/test_backlog.py` (new), `tests/test_skills.py`, `evals/promptfoo/idea.yaml` (new), `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `evals/checks.py`, `evals/runner.py`. Done: `uv run pytest tests/test_backlog.py tests/test_skills.py tests/test_static.py` exits 0.
- T2: Digest and decide. `digest` prints one line per `inbox` idea and per `parked` idea past `review_by`. `decide <file> keep|park|renew|drop --by <date> --effort --impact --reason` sets `status`, `review_by`, a `[triage]` line with the owner's name, and adds or removes the README row (A3, A4). `BACKLOG.md` gets the triage steps; skill `triage` runs them and waits for the owner. Eval `triage` (scenarios `triage_digest`, `triage_apply`). Files: `plugin/scripts/backlog.py`, `plugin/stages/BACKLOG.md`, `plugin/skills/triage/SKILL.md` (new), `tests/test_backlog.py`, `tests/test_skills.py`, `evals/promptfoo/triage.yaml` (new), `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `evals/checks.py`, `evals/runner.py`. after: T1. Done: `uv run pytest tests/test_backlog.py tests/test_skills.py` exits 0.
- T3: Commit. `commit <file>` needs `status: triaged` and no task folder (A6). It sets `status: committed`, appends a `[commit]` line that names `docs/tasks/<task>/` (close links it, ADR 0026), writes `STATE.md` from `.kairyn/templates/STATE.md` with a log line that names the idea file, and prints both commands. Else: no change, one `FAIL:` line, exit 1. Files: `plugin/scripts/backlog.py`, `plugin/stages/BACKLOG.md`, `tests/test_backlog.py`. after: T2. Done: `uv run pytest tests/test_backlog.py` exits 0.
- T4: Grill and requirements read the linked idea. Each stage's Inputs gets one line: the idea file that `STATE.md` names, as the request. Cuts to stay in budget are named in the slice commit. Scenarios `grill_from_idea` (one turn) and `requirements_from_idea`. Files: `plugin/stages/GRILL.md`, `plugin/stages/REQUIREMENTS.md`, `plugin/skills/grill/SKILL.md`, `evals/promptfoo/grill.yaml`, `evals/promptfoo/requirements.yaml`, `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `evals/checks.py`, `evals/runner.py`, `tests/test_grill_checks.py`, `tests/test_requirements_checks.py`, `plugin/.claude-plugin/plugin.json` (0.21.5), `plugin/release-hashes.json`, `.kairyn/` (this repo upgraded to it). after: T3. Done: `uv run pytest` exits 0.
- T5: Docs. `TRIAGE.md` keeps Next and Parked plus a pointer to `BACKLOG.md`. Name the stage and skills in `README.md`, `.harness/README.md` and `plugin/harness/.harness/workflows/running-stages.md`; refresh `plugin/release-hashes.json`. Files: `docs/backlog/TRIAGE.md`, `README.md`, `.harness/README.md`, `plugin/harness/.harness/workflows/running-stages.md`, `plugin/release-hashes.json`, `tests/test_static.py`. after: T4. Done: `uv run pytest && claude plugin validate plugin` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 `BACKLOG.md` is an optional stage with the rules | T1 | `tests/test_static.py` stage checks; `test_backlog.py::test_stage_names_the_rules` |
| AC2 capture script writes, creates, never overwrites | T1 | `test_backlog.py::test_capture_*`; eval `idea_capture` (request word for word, problem marked) |
| AC3 triage lists, proposes, waits | T2 | eval `triage_digest`: each inbox and stale parked idea named with a proposal and reason; repo unchanged |
| AC4 each decision's status, date, log, row | T2 | `test_backlog.py::test_decide_*`; eval `triage_apply` |
| AC5 commit writes; refuses bad input | T3 | `test_backlog.py::test_commit_*` |
| AC6 grill and requirements take the idea | T4 | evals `grill_from_idea`, `requirements_from_idea` |
| AC7 `TRIAGE.md` keeps Next and Parked | T5 | `test_static.py::test_triage_keeps_next_and_parked` |

Approval: Jayson De los Reyes, 2026-11-28T01:40:52Z, "Approve"
