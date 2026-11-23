---
task: 2026-11-24-public-ready
stage: requirements
summary: "Protect main with 6 required CI checks, harden the supply chain, add outsider files, and make private knowledge-base pointers optional."
---

# Requirements: Public-ready hardening

## Problem statement
jisundr/kairyn became public in one step. `main` has no protection, and Dependabot security updates are off. Actions are pinned by tag. Outsiders have no private way to report a vulnerability and no issue form. Three instruction lines send an agent to the private `../knowledge-base`.

## Scope
In: protection rules for `main` (D3)
In: Dependabot and SHA pins for actions (D4)
In: private vulnerability reporting and outsider files (D5)
In: the 3 instruction lines about the knowledge base (D6)
Out: `CODE_OF_CONDUCT.md`, `CODEOWNERS`, Discussions (D5)
Out: `promptfoo` pin updates, evals in CI (D4, D6)
Out: changes to records: backlog items, ADR 0007 (D6)
Out: Actions billing for `jisundr/kairyn-archive`

## Requirements
- R1: The `main` branch shall accept changes only through a pull request with 0 required approvals. (D3)
- R2: When a pull request targets `main`, GitHub shall block the merge until these checks pass: `tests (ubuntu-latest)`, `tests (macos-latest)`, `consumer install (plain python3 3.9)`, `consumer install (plain python3 3.13)`, `shellcheck`, `version-bump`. (D3)
- R3: The `main` branch shall reject force pushes and deletion. (D3)
- R4: The `main` protection shall apply to admins. (D3)
- R5: The repo shall have Dependabot alerts and Dependabot security updates on. (D4)
- R6: The repo's Dependabot shall open version-update pull requests weekly for the `github-actions` and `uv` ecosystems. (D4)
- R7: The CI workflows shall pin each action in a `uses:` line by a 40-character commit SHA, with a version comment at the end of the line. (D4)
- R8: The repo shall have private vulnerability reporting on. (D5)
- R9: The `SECURITY.md` file shall tell reporters to use private vulnerability reporting, never a public issue, and say that only the latest version gets fixes. (D5)
- R10: When an outsider opens a new issue, GitHub shall offer a bug-report form. The form asks for 5 fields: kairyn version, Claude Code version, OS, steps, output. (D5)
- R11: The issue chooser shall not offer blank issues. (D5)
- R12: The `CONTRIBUTING.md` file shall say: open an issue before a pull request, run `uv run pytest`, and the maintainer runs the evals. (D5, D6)
- R13: When a contributor opens a pull request, GitHub shall fill its body from a template with the 3-item checklist in A2. (D5, A2)
- R14: The 3 instruction lines shall say the playbooks are private and are read only if `../knowledge-base` exists. The lines are `.harness/README.md` principle 5, the `.kairyn/learnings.md` grill line and `docs/backlog/README.md` line 3. (D6)
- R15: The `.harness/budgets.yml` file shall have a budget for each new markdown file. (A1)
- R16: The `.harness/workflows/pull-request.md` file shall name the required checks and the `main` protection. (A1)

## Non-functional needs
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a need.
- Security: R1 to R9 are the security needs. (D3, D4, D5)
- Observability: not applicable: no source states a need.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | The `CLAUDE.md` rules apply: each markdown file has a budget; a workflow change updates its harness doc. | user |
| A2 | assumption | The pull request checklist: `uv run pytest` passes; the pull request links an issue; a change under `plugin/` bumps the version. | user |
| A3 | assumption | Repo settings (R1 to R6, R8, R11 partly) are not in git. The build sets them with `gh api`; the review reads them back with `gh api`. | design |
| K1 | risk | If a CI job name changes, its required check never reports and blocks every merge. | design |
| K2 | risk | With R4, a CI outage blocks every merge, also urgent fixes. The admin can turn R4 off for that merge. | user |
| K3 | risk | The `vercel` and `claude` check suites stay `queued`. They are not required, so they do not block. | user |
| K4 | risk | An AFK build that changes GitHub settings acts outside the repo. | design |
| D1 | dependency | A `gh` token with admin rights on jisundr/kairyn. | user |

## Acceptance criteria
- [ ] `gh api repos/jisundr/kairyn/branches/main/protection` shows a required pull request with 0 approvals. (R1)
- [ ] The same call lists exactly the 6 checks in R2. (R2)
- [ ] It shows `allow_force_pushes` and `allow_deletions` false. (R3)
- [ ] It shows `enforce_admins` true. (R4)
- [ ] `gh api repos/jisundr/kairyn` shows `dependabot_security_updates` enabled, and `gh api repos/jisundr/kairyn/vulnerability-alerts` returns 204. (R5)
- [ ] `.github/dependabot.yml` has `github-actions` and `uv` entries with `interval: weekly`. (R6)
- [ ] A pytest fails when a workflow `uses:` line has no 40-character SHA or no version comment, and passes on `ci.yml`. (R7)
- [ ] `gh api repos/jisundr/kairyn/private-vulnerability-reporting` returns `enabled: true`. (R8)
- [ ] `SECURITY.md` has the reporting link, the "no public issue" rule and the supported version. (R9)
- [ ] `.github/ISSUE_TEMPLATE/bug_report.yml` asks for the 5 fields in R10. (R10)
- [ ] `.github/ISSUE_TEMPLATE/config.yml` has `blank_issues_enabled: false`. (R11)
- [ ] `CONTRIBUTING.md` has the 3 rules in R12. (R12)
- [ ] `.github/pull_request_template.md` has the 3 items in A2. (R13)
- [ ] Each of the 3 lines in R14 makes `../knowledge-base` conditional. `git diff` shows no change to backlog items or ADR 0007. (R14)
- [ ] `uv run pytest` passes, including the budget test. (R15)
- [ ] `pull-request.md` lists the 6 required checks and the protection rules. (R16)

## Open questions and answers
- Q1 to Q6: answered in `CONCEPT.md` as D1 to D6. (user)

Approval: Jayson De los Reyes, 2026-11-23T23:38:19Z, "approved, run design"
