---
task: 2026-11-24-public-ready
stage: grill
summary: "Harden the public jisundr/kairyn repo and make it ready for outside users and contributors."
---

# Concept: Public-ready hardening

## Concept
Make jisundr/kairyn safe for outsiders who install the plugin and report problems; accept pull requests, but do not invite them. Protect `main`: a change merges only through a pull request whose 6 CI checks pass, with no force push or deletion, for admins too. Harden the supply chain with Dependabot alerts, security updates and weekly version updates for actions and `uv`, and pin each action by commit SHA. Give outsiders private vulnerability reporting, `SECURITY.md`, a bug-report issue form, a short `CONTRIBUTING.md` and a pull request template. Rewrite the 3 instruction lines that point to the private knowledge base so they work without it, and keep the records unchanged.

## Decisions
- D1: Serve outsiders who install the plugin and report problems first. Accept pull requests, but do not invite them yet. (user accepted)
- D2: Actions works on the public repo. Billing blocks only the private archive. A dispatched run (45287334802) and a draft pull request run (45287760930, PR #8) passed all jobs. CI can be a required check now. (user, by the test)
- D3: Protect `main`: a pull request with 0 approvals, no force push, no deletion, and the rules apply to admins. The required checks are both `tests` jobs, both `consumer install` jobs, `shellcheck` and `version-bump`, with no up-to-date rule. (user accepted)
- D4: Turn on Dependabot alerts and security updates. Add `dependabot.yml` with weekly version updates for `github-actions` and `uv`. Pin each action by full commit SHA with a version comment. Leave `promptfoo` out of scope. (user accepted)
- D5: Turn on private vulnerability reporting. Add `SECURITY.md`, a bug-report issue form with blank issues off, a short `CONTRIBUTING.md` and a pull request template. Add no `CODE_OF_CONDUCT.md` and no `CODEOWNERS`. (user accepted)
- D6: Rewrite the 3 instruction lines that name the private knowledge base (`.harness/README.md` principle 5, `.kairyn/learnings.md` grill line, `docs/backlog/README.md` line 3). Each says the playbooks are private and read only if `../knowledge-base` exists. Keep the records (backlog items, ADR 0007) unchanged. Evals stay local: CI runs no evals, the maintainer runs them before a merge. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| required check | A CI job that must pass before a pull request can merge into `main`. |
| outsider | A person without write access to jisundr/kairyn. |

## Open branches
- None.
