# 13. GitHub settings are a checked script, and main takes only passing pull requests

Date: 2026-11-24

## Status
Accepted

## Context
Task 2026-11-24-public-ready. The repo became public with no protection on `main`. GitHub settings are not in git (A3). If a CI job name changes, its required check never reports and blocks every merge (K1). The repo has one maintainer (D1).

## Decision
- `scripts/github_settings.py` holds the settings as code. `--apply` sets them with `gh api`. `--check` reads them back and exits 1 on a difference (option B).
- `main` takes changes only through a pull request with 0 approvals. The 6 CI jobs are required checks, with no up-to-date rule. Force push and deletion are blocked. The rules apply to admins (D3).
- Dependabot alerts, security updates and private vulnerability reporting are on (D4, D5).
- A pytest compares `REQUIRED_CHECKS` with the job names in `ci.yml` (K1).
- Option A (`gh api` calls by hand) had no repeatable check. Option C (Terraform or a GitHub App) was too large.

## Consequences
- A renamed CI job fails a test before it blocks merges.
- Each change to `main` needs a pull request, also a log line in `STATE.md`.
- A CI outage blocks every merge. The admin can turn the admin rule off for that merge (K2).
- `--apply` acts on the live repo, so it runs only after a human approval (K4).
