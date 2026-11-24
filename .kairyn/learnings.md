# Learnings

Stages append here.
- grill: `afk.py` reads `.kairyn/afk.yml` with its own flat parser (`plugin/scripts/afk.py:125`), not `simple_yaml.py`. Check the parser before you recommend a nested afk.yml shape: it sets which slice goes first.
- requirements: afk.py's PR body is BUILD.md and its merge uses `gh pr merge <branch> --merge` from the repo root (`plugin/scripts/afk.py:607`, `:679`). A second repo needs its own cwd for each gh call.
- design: afk.py runs each done command in a detached checkout of the repo that holds the code (`run_at`). In a child-repo task the done command runs in the child repo, so it must use the child's test tool.
- review: Ban a `continue` past a repo with no remote in afk.py `decide()` with a test, because a child-repo task can merge its home branch while the child code stays unmerged and no log line says so.
- review: Ban a release of a moved or renamed eval test with no run of its new file, with a gate, because the AC11 evidence came from `design-repo.yaml` and the shipped `design.yaml` copy never ran.
- review: Ban a re-merge of an already merged child pull request in afk.py with a retry test, because a home merge failure followed by a new approve calls `gh pr merge` on the child again.
- review: Ban hashes of never-released file text in `plugin/release-hashes.json` with a check, because a reverted fix-round text stays listed as a known release.
- review: Ban a fix-round test edit (flag on `evals/promptfoo/design-repo.yaml` and `design.yaml`) with no new eval run, with a gate, because the move left the flag open with no fresh evidence.
- review: Ban an approve retry that needs a hand edit of REVIEW.md with a documented step or a retry command, because a blocked merge leaves no `Decision: pending` line and afk.py refuses the retry.
