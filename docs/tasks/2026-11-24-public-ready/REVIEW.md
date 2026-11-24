---
task: 2026-11-24-public-ready
stage: review
summary: "Repo files and tests pass (546). T6 did not run: live main protection, Dependabot and vulnerability reporting are all off, so AC1-AC5 and AC8 fail."
---

# Review: Public-ready hardening

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 pull request with 0 approvals | Payload test passes (BUILD.md T3). Live: `gh api .../branches/main/protection` returns 404 "Branch not protected". None: finding F1 |
| AC2 exactly the 6 checks | `test_required_checks_equal_ci_job_names` passes (T3). Live: no protection. None: finding F1 |
| AC3 no force push or deletion | Payload test passes (T3). Live: no protection. None: finding F1 |
| AC4 admins included | Payload test passes (T3). Live: no protection. None: finding F1 |
| AC5 Dependabot alerts and security updates on | Live: `dependabot_security_updates` is `disabled`; `vulnerability-alerts` returns 404. None: finding F1 |
| AC6 `dependabot.yml` weekly entries | `test_dependabot_weekly_version_updates` (T2 row) |
| AC7 SHA pins with version comments | `test_unpinned_*` and `test_workflow_actions_pinned_by_sha` (T1 row). The SHAs agree with tags `v7` and `v10.3.3` (`gh api .../commits/<tag>`). |
| AC8 private vulnerability reporting on | Live: `{"enabled":false}`. None: finding F1 |
| AC9 `SECURITY.md` content | `test_security_md_points_to_private_reporting` (T4 row) |
| AC10 bug-report form fields | `test_bug_report_form_asks_for_the_five_fields` (T4 row) |
| AC11 blank issues off | `test_issue_chooser_has_no_blank_issues` (T4 row) |
| AC12 `CONTRIBUTING.md` rules | `test_contributing_md_states_the_three_rules` (T4 row). See finding F3. |
| AC13 pull request checklist | `test_pull_request_template_has_the_checklist` (T4 row) |
| AC14 knowledge-base lines conditional; records unchanged | `test_knowledge_base_lines_are_conditional_and_private` (T5 row). The diff does not change `docs/adr/0007-run-evals-agent-skill.md` or a backlog item. Only line 3 of `docs/backlog/README.md` changes. |
| AC15 budgets | `test_new_markdown_has_its_own_budget`, `uv run pytest` 546 passed (gate testing) |
| AC16 `pull-request.md` lists checks and protection | `test_pull_request_doc_names_checks_and_protection` (T5 row) |

## Gates
- accessibility: not set. REQUIREMENTS.md says not applicable.
- performance: not set. REQUIREMENTS.md says not applicable.
- observability: not set. REQUIREMENTS.md says not applicable.
- security: not set. R1 to R9 are the security needs of this task. No gate checks them. Only `python3 scripts/github_settings.py --check` does, and it exits 1 now.

## Risky files
- `scripts/github_settings.py`: `--apply` changes the live repo. With `enforce_admins` true, a wrong `REQUIRED_CHECKS` entry blocks every merge, also for the admin.
- `.github/workflows/ci.yml`: its job names are the required checks. A rename blocks merges (K1). A bad SHA pin stops all CI.
- `tests/test_github_settings.py`: `ci_check_names` is the only guard for K1. If it expands a matrix wrongly, the guard passes and a merge block follows.

## Findings
- F1: T6 did not run. BUILD.md has no T6 row. `python3 scripts/github_settings.py --check` exits 1 with 4 failures: no protection on `main`, Dependabot security updates off, Dependabot alerts off, private vulnerability reporting off. AC1 to AC5 and AC8 are not met. Before the merge, the human must approve T6 and run `--apply`, then `--check` must exit 0. Do the apply after CI passes on PR #11; then the 6 checks exist on `main`.
- F2: BUILD.md says "Flags: None", but the approval task T6 is open. The build does not record an open approval task.
- F3: Some content tests are loose. `test_contributing_md_states_the_three_rules` passes if the words "open an issue" and "before" are anywhere in the file. `test_security_md_points_to_private_reporting` passes if "latest" is anywhere. The files are correct now, but the tests do not hold the rules.
- F4: The protection payload sets `contexts` with no app. A check of the same name from any app satisfies the rule. This is not in REQUIREMENTS.md. Low risk on a repo with one maintainer.

Decision: Jayson De los Reyes, 2026-11-24T01:15:47Z, "approved"