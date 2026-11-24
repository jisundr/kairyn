# Changelog

## Unreleased

- testing-and-evals.md points to each eval's yaml for its gates and now holds four eval rules from the first retro. (split-testing-and-evals)
- After design approval, /kairyn:build runs build, gates and review with no user turns; /kairyn:review records the merge decision. (2026-11-23-build-stage; closes build-stage, gates-stage, review-stage)
- main takes only pull requests with 6 passing CI checks; Dependabot, SHA-pinned actions, SECURITY.md, CONTRIBUTING.md and issue and pull request templates added. (2026-11-24-public-ready; closes public-ready) (2026-11-24-public-ready)
- Retro emptied learnings.md: four rules moved to testing-and-evals.md and pull-request.md; ten ideas went to the backlog inbox. (2026-11-24-retro) (2026-11-24-retro)
- A home-repo task can build its code in one child repo: list it under repos: in afk.yml; approve merges the child, then the home. (2026-11-24-multi-repo; closes multi-repo) (2026-11-24-multi-repo)
