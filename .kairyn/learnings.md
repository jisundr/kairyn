# Learnings

Stages append here.
- grill: `afk.py` reads `.kairyn/afk.yml` with its own flat parser (`plugin/scripts/afk.py:125`), not `simple_yaml.py`. Check the parser before you recommend a nested afk.yml shape: it sets which slice goes first.
- requirements: afk.py's PR body is BUILD.md and its merge uses `gh pr merge <branch> --merge` from the repo root (`plugin/scripts/afk.py:607`, `:679`). A second repo needs its own cwd for each gh call.
- design: afk.py runs each done command in a detached checkout of the repo that holds the code (`run_at`). In a child-repo task the done command runs in the child repo, so it must use the child's test tool.
