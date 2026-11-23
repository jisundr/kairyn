---
task: 2026-11-24-public-ready
stage: design
summary: "Repo files and pytest checks by pull request; a settings script applies and checks GitHub settings after a human approval."
---

# Design: Public-ready hardening

## Approach
Option B. Files in git (R6, R7, R9 to R16) get pytest checks. GitHub settings (R1 to R5, R8) are not in git (A3), so `scripts/github_settings.py` holds them as code. `--apply` sets them, and `--check` reads them back. A pytest compares its required checks with the job names in `ci.yml`, so a renamed job fails a test before it blocks merges (K1). Only `--apply` acts outside the repo, so its slice needs approval (K4).

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Files by pull request; settings by `gh api` calls typed once by hand. | Lowest: no script. | No repeatable check. K1 stays open: a renamed job blocks merges with no warning. |
| B | As A, plus `scripts/github_settings.py` with `--apply` and `--check`, and a test that ties its checks to `ci.yml`. | One script, about 120 lines, and 2 test files. | `--apply` acts on the live repo; it runs only after approval. |
| C | Settings as code with Terraform or a GitHub App. | New tool, state and token. | Too large for a small batch. |

## Tasks
- T1: Pin each action in `ci.yml` by commit SHA with a version comment. A test fails on a `uses:` line with no SHA or no comment. Files: `.github/workflows/ci.yml`, `tests/test_github_files.py` (new). Done: `uv run pytest tests/test_github_files.py` exits 0.
- T2: Add Dependabot version updates, weekly, for `github-actions` and `uv`. Files: `.github/dependabot.yml` (new), `tests/test_github_files.py`. after: T1. Done: `uv run pytest tests/test_github_files.py` exits 0.
- T3: Add the settings script. `REQUIRED_CHECKS` lists the 6 checks. Pure functions build the protection payload for R1 to R4. `--check` reads the protection, Dependabot alerts, security updates and private vulnerability reporting, and exits 1 on a difference. Tests: the checks equal the job names in `ci.yml`; the payload has 0 approvals, admins on, no force push, no deletion. Files: `scripts/github_settings.py` (new), `tests/test_github_settings.py` (new). after: T1. Done: `uv run pytest tests/test_github_settings.py` exits 0.
- T4: Add the outsider files and their budgets. Tests read each file for the content its requirement names. Files: `SECURITY.md` (new), `CONTRIBUTING.md` (new), `.github/pull_request_template.md` (new), `.github/ISSUE_TEMPLATE/bug_report.yml` (new), `.github/ISSUE_TEMPLATE/config.yml` (new), `.harness/budgets.yml`, `tests/test_github_files.py`. after: T2. Done: `uv run pytest tests/test_github_files.py tests/test_budgets.py` exits 0.
- T5: Make the 3 knowledge-base lines conditional. Add the required checks and the protection to `pull-request.md`, then run `uv run python plugin/scripts/harness_docs.py --write`. Tests: each line says the path is read only if it exists; `pull-request.md` names each of `REQUIRED_CHECKS`. Files: `.harness/README.md`, `.kairyn/learnings.md`, `docs/backlog/README.md`, `.harness/workflows/pull-request.md`, `tests/test_github_settings.py`. after: T3, T4. Done: `uv run pytest` exits 0.
- T6 (approval): Apply the settings to jisundr/kairyn with `python3 scripts/github_settings.py --apply`. Not a vertical slice: it changes only live settings, no code. Files: none. after: T5. Done: `python3 scripts/github_settings.py --check` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 pull request with 0 approvals | T3, T6 | payload test; `--check` |
| AC2 exactly the 6 checks | T3, T6 | checks equal `ci.yml` job names; `--check` |
| AC3 no force push or deletion | T3, T6 | payload test; `--check` |
| AC4 admins included | T3, T6 | payload test; `--check` |
| AC5 Dependabot alerts and security updates on | T6 | `--check` |
| AC6 `dependabot.yml` weekly entries | T2 | `test_github_files.py` |
| AC7 SHA pins with version comments | T1 | `test_github_files.py` |
| AC8 private vulnerability reporting on | T6 | `--check` |
| AC9 `SECURITY.md` content | T4 | `test_github_files.py` |
| AC10 bug-report form fields | T4 | `test_github_files.py` |
| AC11 blank issues off | T4 | `test_github_files.py` |
| AC12 `CONTRIBUTING.md` rules | T4 | `test_github_files.py` |
| AC13 pull request checklist | T4 | `test_github_files.py` |
| AC14 knowledge-base lines conditional; records unchanged | T5 | `test_github_settings.py`; reviewer reads the diff |
| AC15 budgets | T4 | `test_budgets.py` |
| AC16 `pull-request.md` lists checks and protection | T5 | `test_github_settings.py` |

Approval: Jayson De los Reyes, 2026-11-23T23:41:28Z, "Approve"
