# Changelog

## Unreleased

- testing-and-evals.md points to each eval's yaml for its gates and now holds four eval rules from the first retro. (split-testing-and-evals)
- After design approval, /kairyn:build runs build, gates and review with no user turns; /kairyn:review records the merge decision. (2026-11-23-build-stage; closes build-stage, gates-stage, review-stage)
- main takes only pull requests with 6 passing CI checks; Dependabot, SHA-pinned actions, SECURITY.md, CONTRIBUTING.md and issue and pull request templates added. (2026-11-24-public-ready; closes public-ready) (2026-11-24-public-ready)
- Retro emptied learnings.md: four rules moved to testing-and-evals.md and pull-request.md; ten ideas went to the backlog inbox. (2026-11-24-retro) (2026-11-24-retro)
- A home-repo task can build its code in one child repo: list it under repos: in afk.yml; approve merges the child, then the home. (2026-11-24-multi-repo; closes multi-repo)
- Retro emptied learnings.md: two rules moved to testing-and-evals.md and change-a-stage.md; three ideas went to the backlog inbox. (2026-11-25-retro)
- The exit stage is now close, so a bare /exit no longer clashes; /kairyn:upgrade removes unedited files a release no longer ships. (2026-11-25-skill-names-clash; closes skill-names-clash)
- Milestones: hooks and afk.py write tagged progress lines to one log; a first-mate session streams them with Monitor. Opt in with .kairyn/milestones.yml. (2026-11-25-first-mate-hub)
- Retro emptied learnings.md: four rules moved to upgrade.md and testing-and-evals.md; seven ideas went to the backlog inbox. (2026-11-25-retro-2)
- afk.py: a blocked run resumes on /kairyn:build; an uncommitted or branch-only task folder works; approve retries a failed merge; a malformed task line blocks. close archives tasks where no git exists. (backlog Next batch, 2026-11-25; closes afk-uncommitted-task-folder, afk-task-folder-check, afk-resume-blocked, build-needs-branch-free, afk-drops-task-lines, approve-retry, exit-without-git)
- This repo's AFK runs get four review gates (scripts/gates.py: design, commits, evals, sessions), and a test bans `# noqa` in evals/promptfoo/. (gates-and-lint-rules; closes gate-changes-outside-design, gate-eval-pass-for-plugin-changes, gate-fix-round-test-edits, gate-real-session-criteria, lint-noqa-in-evals, lint-tests-in-feat-commits)
- milestones.py: `watch` and `catchup` write `.session/watch.json` to a temp file, then rename it, so a reader never sees it empty. (backlog Next batch, 2026-11-25; closes flaky-watch-test-macos)
- afk.py writes STATE.md through a shared atomic write (plugin/scripts/atomic_write.py: a temp file, then a rename), so a reader never sees it empty. milestones.py's watch.json write uses it too. (backlog Next batch, 2026-11-25; closes atomic-state-md)
- afk.py approve waits until every check on the pushed head passes, then merges; a failed check blocks. A fix-round edit to stage text fails the evals gate (a test now shows it). This repo's .gitattributes merges learnings.md by union. The design judge sees the fixture's afk.yml. (backlog batch, 2026-11-25; closes approve-waits-for-ci, flag-fix-round-stage-edits, parallel-learnings, judge-sees-afk-yml)
- afk.py readiness blocks a run whose REQUIREMENTS.md names a security need while the security gate is not set; the design eval check skips backticked branch names such as `feat/x`; the SECURITY.md and CONTRIBUTING.md tests match whole rules. (backlog batch, 2026-11-25; closes gate-security-not-set, grounded-branch-names, lint-loose-content-tests)
- The shipped afk-run.md describes child repos (`repos:`) and two pitfalls: `--max-budget-usd` is a soft cap, and a `PreToolUse` hook can rewrite Bash commands past an allowlist. (backlog batch, 2026-11-25; closes shipped-afk-run-child-repos, child-done-commands, max-budget-soft-cap, hook-rewrites-bash)
- The design and requirements stages read their shared approval rules from one new file, `.kairyn/stages/_approval.md`. DESIGN.md drops from 498 to 420 tokens, REQUIREMENTS.md from 495 to 426. (backlog Next, 2026-11-25; the `_approval.md` slice of split-design-stage, which stays open)
