# kairyn

An agentic SDLC that grows with your repo.

**kairyn** is a Tagalized spelling of *cairn*: a pile of stacked stones that marks a trail. Each stage is a marker on the trail, and every run adds a stone back to your repo.

> Early setup. Commands, agents and stage templates are coming next.

## Install (Claude Code)

```
/plugin marketplace add jisundr/kairyn
/plugin install kairyn@kairyn
```

## Layout

```
.
├── .claude-plugin/marketplace.json   # marketplace entry pointing to ./plugin
├── plugin/                           # the kairyn plugin
│   ├── .claude-plugin/plugin.json
│   ├── commands/init.md              # /kairyn:init sets up .kairyn/ in a repo
│   ├── stages/                       # stage definitions copied into .kairyn/stages/
│   │   ├── _template.md              # skeleton for authoring new stages
│   │   └── REQUIREMENTS.md           # stage 1: request -> scoped requirements
│   └── templates/STATE.md            # per-task state file
├── tests/                            # fast tests (pytest)
├── evals/                            # BDD evals that run real claude sessions
├── tools/harness_docs.py             # checks .harness doc headers, builds index tables
├── .harness/                         # how we work on kairyn: dev workflows
├── CLAUDE.md                         # loaded every session; points to .harness on demand
└── README.md                         # docs live at the root
```

## How tasks are stored

Each task gets a folder in your repo, with a `STATE.md` and one file per stage:

```
docs/tasks/<YYYY-MM-DD>-<slug>/
├── STATE.md              # front matter = current state, body = log
└── REQUIREMENTS.md
```

## Tests and evals

**Tests** are fast, free and give the same result every time:

```bash
uv run pytest
```

**Evals** run real `claude` sessions N times and check a pass rate, so they are slow and cost tokens. They are written as BDD scenarios in `evals/features/*.feature`, and each feature declares the plugin files it exercises:

```gherkin
# depends: plugin/stages/REQUIREMENTS.md, plugin/stages/_template.md
```

An eval runs only when those files changed since it last passed (recorded locally in `evals/results/passed.json`):

```bash
uv run pytest -m eval               # only evals whose dependencies changed
uv run pytest -m eval --all-evals   # everything, e.g. before a release
```

Every eval run saves its evidence (task folders, judge scores) under `evals/results/<run-id>/`. Settings: `KAIRYN_EVAL_RUNS` (default 10), `KAIRYN_MODEL`, `KAIRYN_JUDGE_MODEL`.

Adding an eval: write the scenario first and watch it fail against the current stage instructions, then change the instructions until it passes. To add one, create `evals/features/<name>.feature` and `evals/test_<name>.py`.

## Contributing

Development workflows (tests, evals, changing a stage, PRs) are documented in [.harness/](.harness/README.md).

## License

MIT
