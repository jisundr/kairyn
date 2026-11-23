---
task: 2026-11-23-grill-on-sonnet
stage: requirements
summary: "A CONCEPT.md template with four ## sections; GRILL.md points to it; one 10-run pass of grill, init and upgrade on Sonnet."
---

# Requirements: Grill on Sonnet has never passed a 10-run gate

## Problem statement
Grill fails its 10-run gate: `well_formed` 8/10 in runs `20261123T032454Z`, `20261123T035336Z` and `20261123T083521Z`. In `20261123T083521Z`, both failures wrote `# Concept`, and `evals/checks.py` needs `## Concept`. Grill has no `CONCEPT.md` template, so the model picks the format (D1).

## Scope
In: a new `plugin/templates/CONCEPT.md` with the four sections (D2).
In: the Output section of `plugin/stages/GRILL.md` points to the template (D2).
In: one 10-run pass of grill, init and upgrade (D4).
Out: a fix for guessed timestamps (D3). A change of the grill model (D1). Changes to `evals/checks.py`.

## Requirements
- R1: The `plugin/templates/CONCEPT.md` template shall hold front matter and the sections `## Concept`, `## Decisions`, `## Terms` and `## Open branches`. (D2)
- R2: The Output section of `plugin/stages/GRILL.md` shall tell the stage to fill `.kairyn/templates/CONCEPT.md`. (D2)
- R3: The grill skill shall stay on Sonnet. (D1)
- R4: The `evals/promptfoo/grill.yaml` header shall list `plugin/templates/CONCEPT.md` in `# depends:`. (D4, A3)
- R5: The plugin shall carry a newer version and current release hashes. (A1)
- R6: The `GRILL.md` stage and the template shall stay within their token budgets. (A2)
- R7: The grill, init and upgrade evals shall each pass every gate in one 10-run pass. (D4)
- R8: If a grill run in that pass fails `well_formed`, its reason shall not be a missing `concept` section. (D4)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a time limit.
- Security: not applicable: no new input.
- Observability: not applicable: eval summaries already show results and cost.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Repo rule (`upgrade.md`): a change under `plugin/` bumps the version and regenerates `plugin/release-hashes.json`. | build |
| A2 | assumption | Repo rule: over budget, cut text; never raise the limit. `GRILL.md` is at 498/500. | build |
| A3 | assumption | Repo rule: an eval lists every plugin file it uses in `# depends:`. | build |
| A4 | assumption | Init copies every file in `plugin/templates/`, and upgrade installs a new template (`kairyn_files.py`). | build |
| A5 | assumption | This repo's `.kairyn/templates/CONCEPT.md` comes through `/kairyn:upgrade`. | build |
| K1 | risk | Grill fails for another reason, such as a guessed timestamp in 2 runs. Then the task stops and the model choice becomes its own decision (D1, D3). | Jayson |
| K2 | risk | The 10-run pass costs about $4 (run `20261123T083521Z`). | Jayson |

## Acceptance criteria
- [ ] `plugin/templates/CONCEPT.md` has front matter and the four `##` sections. (R1)
- [ ] The `GRILL.md` Output section names `.kairyn/templates/CONCEPT.md`. (R2)
- [ ] `plugin/skills/grill/SKILL.md` still says `model: sonnet`. (R3)
- [ ] The `grill.yaml` `# depends:` line lists `plugin/templates/CONCEPT.md`. (R4)
- [ ] `plugin.json` has a newer version, and `uv run pytest` passes with current release hashes. (R5)
- [ ] `plugin/scripts/budgets.py` reports `GRILL.md` and `CONCEPT.md` within budget. (R6)
- [ ] One `/run-evals grill init upgrade --all-evals` summary shows every gate passing at 10 runs. (R7)
- [ ] That summary has no `missing section 'concept'` reason. (R8)

## Open questions and answers
None

Approval: Jayson De los Reyes, 2026-11-23T09:00:44Z, "approved and proceed"
