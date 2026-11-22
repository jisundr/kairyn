# kairyn

An agentic SDLC that grows with your repo.

**kairyn** is a Tagalized spelling of *cairn*: a pile of stacked stones that marks a trail. Each stage is a marker on the trail, and every run adds a stone back to your repo.

> Early setup. More commands and stages are coming.

## Install (Claude Code)

```
/plugin marketplace add jisundr/kairyn
/plugin install kairyn@kairyn
```

## What you get in your repo

`/kairyn:init` sets up `.kairyn/` (stages, templates, learnings, a manifest), `docs/tasks/`, and a `.harness/` of short workflow docs with size budgets. It adds a marked block to your `CLAUDE.md` (created if needed) that points Claude to those docs. Nothing you already have is overwritten.

`/kairyn:check` verifies doc headers and size budgets with only `python3`. `/kairyn:check write` also refreshes the indexes.

`/kairyn:upgrade` brings those files up to a newer plugin and keeps your edits. A session-start hook tells you when to run it.

## Layout

```
.
├── .claude-plugin/marketplace.json   # marketplace entry pointing to ./plugin
├── plugin/                           # the kairyn plugin
│   ├── .claude-plugin/plugin.json
│   ├── commands/                     # /kairyn:init, /kairyn:check, /kairyn:upgrade, /kairyn:grill
│   ├── hooks/hooks.json              # SessionStart: warn when the repo's kairyn files are older
│   ├── scripts/                      # init, verify, upgrade, version check, doc and budget checkers
│   ├── harness/                      # .harness/ and CLAUDE.md block installed into your repo
│   ├── stages/                       # stage definitions copied into .kairyn/stages/
│   │   ├── _template.md              # skeleton for authoring new stages
│   │   ├── REQUIREMENTS.md           # stage 1: request -> approved EARS requirements
│   │   ├── GRILL.md                  # optional: interview until you share one concept
│   │   └── MODEL-ROUTING.md          # optional: plan the next model-routing stage
│   ├── templates/                    # STATE.md per task, REQUIREMENTS.md to fill in
│   └── release-hashes.json           # installed-file hashes per release
├── tests/                            # fast tests (pytest)
├── evals/                            # BDD evals that run real claude sessions
├── .harness/                         # how we work on kairyn: dev workflows
├── CLAUDE.md                         # loaded every session; points to .harness on demand
└── README.md                         # docs live at the root
```

## How tasks are stored

Each task gets a folder in your repo, with a `STATE.md` and one file per stage:

```
docs/tasks/<YYYY-MM-DD>-<slug>/
├── STATE.md              # front matter = current state, body = log
└── REQUIREMENTS.md       # ends with an approval line
```

## Tests and evals

**Tests** are fast, free and give the same result every time:

```bash
uv run pytest
```

**Evals** run real `claude` sessions N times and check a pass rate, so they are slow and cost tokens. Each one runs only when the plugin files it exercises changed since it last passed:

```bash
uv run python evals/run.py              # only evals whose dependencies changed
uv run python evals/run.py --all-evals  # everything, e.g. before a release
```

Evidence goes to `evals/results/<run-id>/`. Details: [testing and evals](.harness/workflows/testing-and-evals.md).

## Contributing

Development workflows (tests, evals, changing a stage, PRs) are documented in [.harness/](.harness/README.md).

## License

MIT
