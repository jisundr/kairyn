# kairyn

An agentic SDLC that grows with your repo.

**kairyn** is a Tagalized spelling of *cairn*: stacked stones that mark a trail. Each stage is a marker, and every run adds a stone to your repo.

## Install (Claude Code)

```
/plugin marketplace add jisundr/kairyn
/plugin install kairyn@kairyn
```

## What you get in your repo

`/kairyn:init` sets up `.kairyn/` (stages, templates, learnings, a manifest), `docs/tasks/`, and a `.harness/` of short workflow docs with size budgets. It adds a marked block to your `CLAUDE.md` (created if needed) that points Claude to those docs. Nothing you already have is overwritten.

`/kairyn:check` verifies doc headers and size budgets (`write` also refreshes the indexes). `/kairyn:backlog` writes `.kairyn/backlog.html`, a page of every idea in `docs/backlog/`.

`/kairyn:upgrade` brings those files up to a newer plugin and keeps your edits. A session-start hook tells you when to run it.

After you approve a design, `/kairyn:build` builds, gates and reviews it with no user turns, then stops once: you approve the merge with `/kairyn:review`.

## Layout

```
.
├── .claude-plugin/marketplace.json # marketplace entry pointing to ./plugin
├── plugin/                         # the kairyn plugin
│   ├── .claude-plugin/plugin.json
│   ├── commands/                   # /kairyn:init, check, backlog, upgrade, release
│   ├── skills/                     # one per stage: /kairyn:<stage>, e.g. /kairyn:design, /kairyn:retro; /kairyn:idea, /kairyn:triage
│   ├── hooks/hooks.json            # SessionStart: warn when the repo's kairyn files are older
│   ├── scripts/                    # afk.py (the AFK run), init, verify, upgrade, checkers
│   ├── harness/                    # .harness/ and CLAUDE.md block installed into your repo
│   ├── stages/                     # copied into .kairyn/stages/: REQUIREMENTS, DESIGN, BUILD, GATES, REVIEW, GRILL, BACKLOG, ...
│   ├── templates/                  # STATE.md per task, one template per stage output
│   └── release-hashes.json         # installed-file hashes per release
├── tests/                          # fast tests (pytest)
├── evals/                          # BDD evals that run real claude sessions
├── .harness/                       # how we work on kairyn: dev workflows
├── CLAUDE.md                       # loaded every session; points to .harness on demand
└── README.md                       # docs live at the root
```

## How tasks are stored

Each task gets a folder in your repo, with a `STATE.md` and one file per stage:

```
docs/tasks/<YYYY-MM-DD>-<slug>/
├── STATE.md              # front matter = current state, body = log
└── REQUIREMENTS.md       # ends with an approval line
```

When the change merges, `/kairyn:close` leaves an ADR (if a decision was load-bearing) and a `CHANGELOG.md` line, then deletes the folder. When `.kairyn/learnings.md` passes half its budget, close runs retro to move or drop learnings.

## Tests and evals

**Tests** are fast and free:

```bash
uv run pytest
```

**Evals** run real `claude` sessions N times and check a pass rate, so they cost tokens. Each runs only when the plugin files it exercises changed:

```bash
uv run python evals/run.py              # only evals whose dependencies changed
uv run python evals/run.py --all-evals  # everything, e.g. before a release
```

Evidence goes to `evals/results/<run-id>/`. Details: [testing and evals](.harness/workflows/testing-and-evals.md).

## Contributing

Development workflows (tests, evals, changing a stage, PRs) are documented in [.harness/](.harness/README.md).

## License

MIT
