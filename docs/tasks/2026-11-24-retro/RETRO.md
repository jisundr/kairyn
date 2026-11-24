---
task: 2026-11-24-retro
stage: retro
summary: "19 learnings: 4 move to harness docs, 5 drop, 10 go to the backlog, 0 stay."
---

# Retro: 2026-11-24

learnings.md before: 880/1000. After approval: about 10/1000.

| Entry | Action | Home or path | Text or reason |
|---|---|---|---|
| L1 | backlog | `.harness/README.md` | OVER 29: grill reads the private notes first; they changed 4 of 20 answers. |
| L2 | backlog | `.harness/workflows/task-lifecycle.md` | KAIRYN-OWNED: task files have a 1500-token budget. |
| L3 | backlog | `evals/checks.py` | script: `grounded_problems` reads a backticked branch name as a path. |
| L4 | drop | `.harness/workflows/pull-request.md` | It holds the `release_hashes.py --write` rule. |
| L5 | drop | `tests/test_budgets.py` | Stale: the budget test reports a full file. |
| L6 | move | `.harness/workflows/testing-and-evals.md` | A stub `claude` that picks its action from words in the prompt breaks when two prompts share a word. Match a fixed marker, not a word. |
| L7 | backlog | `.harness/workflows/afk-run.md` | KAIRYN-OWNED: `--max-budget-usd` is a soft cap. |
| L8 | drop | `.harness/workflows/afk-run.md` | Stale: AFK-run text now has its own harness doc. |
| L9 | backlog | `.harness/workflows/afk-run.md` | KAIRYN-OWNED: a PreToolUse hook can rewrite Bash commands. |
| L10 | move | `.harness/workflows/testing-and-evals.md` | Test a new AFK path with one real run on a fixture built to hit it. Stub tests passed, but one real reviewer run found three defects. |
| L11 | move | `.harness/workflows/pull-request.md` | If push or pull request events start no Actions run, test a trigger first (`workflow_dispatch`, a draft pull request). On the new public repo the cause was not billing. |
| L12 | drop | `.kairyn/stages/REQUIREMENTS.md` | Step 5 holds the EARS rule with an example. |
| L13 | backlog | `plugin/scripts/afk.py` | gate: a done build with an approval task and no `BUILD.md` row. |
| L14 | backlog | `plugin/scripts/afk.py` | gate: a not-set security gate on a task with security needs. |
| L15 | backlog | `tests/` | lint rule: content tests that match loose words anywhere in a file. |
| L16 | backlog | `scripts/github_settings.py` | test: required status checks with no app id. |
| L17 | drop | `docs/backlog/20261124010243-afk-drops-task-lines.md` | It holds the dropped `- T6 (approval):` line. |
| L18 | move | `.harness/workflows/pull-request.md` | `main` is protected for admins too. Every change, also a `STATE.md` log line, goes on a branch and merges by pull request. |
| L19 | backlog | `plugin/scripts/afk.py` | script: `approve` merges before CI reports on the new head. |

Approval: Jayson De los Reyes, 2026-11-24T01:44:24Z, "approved, apply the retro and open the PR"
