---
task: 2026-11-23-grill-on-sonnet
stage: design
summary: "Add plugin/templates/CONCEPT.md, point the GRILL.md Output section to it, bump to 0.7.2, prove it with one 10-run pass."
---

# Design: Grill on Sonnet has never passed a 10-run gate

## Approach
Option A. A template fixes the format as `plugin/templates/DESIGN.md` does for design. The `GRILL.md` Output section replaces its four-line section list with one line that names the template, so `GRILL.md` gets shorter. Init and upgrade copy every file in `plugin/templates/` (A4), so no script changes.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | New `plugin/templates/CONCEPT.md`. The `GRILL.md` Output section says: fill `.kairyn/templates/CONCEPT.md` (new). The template keeps the limits: at most 5 sentences, a source per decision. | 1 new file, 1 stage edit, 1 test, version bump. | Grill fails for another reason (K1). |
| B | Option A, and `GRILL.md` also keeps its section list. | About 60 more tokens: `GRILL.md` goes over 500. | Two places state the format. |

## Tasks
- T1: Write the failing test: the template has the four sections in `checks.CONCEPT_SECTIONS`, and the `GRILL.md` Output section names it. Files: `tests/test_static.py`, `evals/checks.py`. Done: the test fails because the template is missing.
- T2: Write the template and edit the Output section. Files: `plugin/templates/CONCEPT.md` (new), `plugin/stages/GRILL.md`. Done: the T1 test passes and `plugin/scripts/budgets.py` reports both files within budget.
- T3: Add the template to the grill eval header. Files: `evals/promptfoo/grill.yaml`. Done: the `# depends:` line lists `plugin/templates/CONCEPT.md`.
- T4: Bump the version to 0.7.2 and write release hashes. Files: `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`. Done: `uv run pytest` passes.
- T5: Run `plugin/scripts/upgrade.py --root .`. Done: `.kairyn/templates/CONCEPT.md` exists and `.kairyn/stages/GRILL.md` is new, with no conflict.
- T6: Ask for a yes, then run `/run-evals grill init upgrade --all-evals`. Done: the report shows every gate passing and no `missing section 'concept'`.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 template has front matter and four sections | T1, T2 | `tests/test_static.py` template test |
| AC2 Output section names the template | T1, T2 | `tests/test_static.py` Output test |
| AC3 grill skill stays on Sonnet | T2 | `tests/test_skills.py` and `git diff main -- plugin/skills/grill/SKILL.md` is empty |
| AC4 `grill.yaml` depends on the template | T3 | `head -1 evals/promptfoo/grill.yaml` |
| AC5 newer version, current hashes | T4 | `uv run pytest` (`tests/test_release_hashes.py`) |
| AC6 budgets | T2 | `plugin/scripts/budgets.py` |
| AC7 every gate passes at 10 runs | T5, T6 | the T6 `summary.md` |
| AC8 no missing `concept` section | T6 | `grep "missing section 'concept'"` in that `summary.md` |

Approval: Jayson De los Reyes, 2026-11-23T09:05:13Z, "yes"
