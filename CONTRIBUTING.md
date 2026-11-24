# Contributing

Bug reports are welcome. Use the bug-report form.

Pull requests are accepted, but:

1. Open an issue before you open a pull request, so we can agree on the change first.
2. Run `uv run pytest` and make it pass. It runs no LLM and costs nothing.
3. Do not run the evals. They cost real tokens; the maintainer runs them before a merge.

A change under `plugin/` must bump the version in `plugin/.claude-plugin/plugin.json`.
