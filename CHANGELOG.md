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
