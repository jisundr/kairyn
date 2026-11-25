---
task: 2026-11-25-first-mate-hub
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | f75b743 | 1 | 687f6ca | 0 |
| T2 | b279515 | 1 | e9d4fb3 | 0 |
| T3 | a9ae614 | 1 | 4dc648b | 0 |
| T4 | 77d9cce | 1 | 43d8af4 | 0 |
| T5 | e8f9f57 | 1 | 6397edf | 0 |

## Flags
- None

## Review
- Review 1: The last acceptance criterion (a real cerna-hq session with tests, a push and a post gives a message per milestone and 0 "status?" asks; R1, R2, R8) has no test. DESIGN.md makes it a manual check by Jayson. The eval `milestones.yaml` only checks that a session reports 2 missed lines and starts Monitor, so this criterion stays unproven until that manual session is run and its transcript counted.; A change outside DESIGN.md: `CLAUDE.md` rewords prose that has nothing to do with milestones. It drops "Verified by `tests/` and `evals/`", changes "manifest and component validation" to "manifest check", and removes "`uv run pytest` never runs evals." from the evals rule. Only the generated index row for `milestones.md` belongs to this task.; A change outside DESIGN.md: `.harness/README.md` rewrites the "Doc format" text. It drops "an agent can read without opening the body" and the sentence "Read only those first lines (`head -6 <file>`) to decide whether a doc matters". No task covers this. Only the index row is generated.; A change outside DESIGN.md: `plugin/release-hashes.json` adds hashes to the version entry before 0.11.0. They cover `.harness/budgets.yml`, `running-stages.md`, `task-lifecycle.md`, `.kairyn/stages/RETRO.md` and a new `.kairyn/stages/CLOSE.md` entry, none of which this task changes. Only the 0.11.0 hashes for `.harness/README.md` and `.harness/workflows/milestones.md` follow from T5.; Files changed that DESIGN.md does not list. `evals/promptfoo/provider.py` adds the `milestones_catchup` scenario. `plugin/scripts/kairyn_files.py` and `plugin/scripts/budgets.py` add `milestones.md` to the shipped docs and the fallback budgets. `tests/stubs/claude` now logs `KAIRYN_MILESTONES`. The edit to `plugin/harness/CLAUDE.block.md` looks like the generated index row. All of these are needed for T2 and T5, but DESIGN.md does not name them. In the other direction, T5 lists `.harness/budgets.yml` and `plugin/harness/.harness/budgets.yml`, and neither changed. That is fine: the `.harness/workflows/*.md` pattern already gives the new docs a budget.
