---
task: 2026-11-25-skill-names-clash
stage: requirements
summary: "Rename the exit stage to close so a bare /exit no longer quits the session; upgrade removes files it no longer ships."
---

# Requirements: Rename the exit stage to close

## Problem statement
A user who types a bare `/exit` to run the kairyn stage gets the Claude Code built-in. The session quits. The stage name `exit` causes this clash. Also, `/kairyn:upgrade` cannot remove a file that a new plugin version no longer ships. So a rename leaves the old stage file in consumer repos.

## Scope
In: rename the `exit` skill and stage to `close` in all that the plugin ships or tests. (D1, D3)
In: a general removal step in `upgrade.py` for files the new version no longer ships. (D4)
Out: renames of `init`, `review` or other skills. (D1)
Out: changes to history: `CHANGELOG.md`, old task logs, `evals/results/` runs, `plugin/release-hashes.json` entries. (D3)
Out: new names for `close.py` subcommands. (D5)
Out: `## Exit criteria` headings. They name a stage section, not the stage. (A1)

## Requirements
- R1: The plugin shall ship the skill `close` in `plugin/skills/close/SKILL.md` and no skill named `exit`. (D1, D2)
- R2: The plugin shall ship the stage file `plugin/stages/CLOSE.md` with `name: close` and no `plugin/stages/EXIT.md`. (D3)
- R3: The plugin shall ship the script `plugin/scripts/close.py` with the subcommands `check`, `adr-path`, `close` and `release`, and no `exit.py`. (D3, D5)
- R4: The `close` stage shall tag its log and learnings lines with `[close]`. (D3)
- R5: The shipped harness docs, `budgets.yml`, `README.md`, the `/kairyn:release` command, `retro` texts, evals and tests shall name the stage `close`, the file `CLOSE.md` and the script `close.py`. (D3)
- R6: When the installed plugin no longer ships a file that `.kairyn/manifest.json` records, and the local copy matches its `.kairyn/.base/` copy or a released hash, `upgrade.py` shall delete the local file, its `.base/` copy and its manifest entry, and print `REMOVED <path>`. (D4)
- R7: When the installed plugin no longer ships a recorded file and the local copy is edited, `upgrade.py` shall keep the file, mark the entry as an open conflict, print `CONFLICT <path>`, and print a line that tells the user to move the edits into the new file and delete the old one. (D4)
- R8: When the user deletes a file from R7, the next `upgrade.py` run shall drop its `.base/` copy and manifest entry and print `REMOVED <path>`. (A2)
- R9: If the local copy of a recorded, no-longer-shipped file is already missing, `upgrade.py` shall drop its `.base/` copy and manifest entry and print `REMOVED <path>`. (A3)
- R10: `upgrade.py` shall not delete a file that the manifest does not record. (A4)

## Non-functional needs
- Accessibility: not applicable: no user interface changes.
- Performance: not applicable: no source states a need.
- Security: not applicable: no source states a need.
- Observability: each removed or kept file gets one `REMOVED` or `CONFLICT` line in the upgrade output. (D4)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | `## Exit criteria` headings and process exit codes keep the word "exit". | Jayson De los Reyes |
| A2 | assumption | An R7 conflict closes only when the user deletes the old file. Then the manifest takes the new version. | Jayson De los Reyes |
| A3 | assumption | A recorded file that the user already deleted counts as removed, not as a conflict. | Jayson De los Reyes |
| A4 | assumption | A repo without a manifest gets no removal step. Its files stay, as upgrade treats unrecorded files today. | Jayson De los Reyes |
| A5 | assumption | This repo's own `.kairyn/` gets the rename through `/kairyn:upgrade`. That run tests the removal step. | design |
| K1 | risk | The changed `close` eval and the `upgrade` eval cost tokens. `plugin/` changes, so they run before merge. | Jayson De los Reyes |
| K2 | risk | A user with a task in progress who types `/kairyn:exit` after the upgrade gets no skill. | Jayson De los Reyes |
| K3 | risk | `evals/results/passed.json` keys the old eval as `exit`. The `close` eval needs a new pass record. | design |

## Acceptance criteria
- [ ] `plugin/skills/close/SKILL.md` exists with `name: close`. `plugin/skills/exit/` does not exist. (R1)
- [ ] `plugin/stages/CLOSE.md` exists with `name: close`. `plugin/stages/EXIT.md` does not exist. (R2)
- [ ] `python3 plugin/scripts/close.py` runs `check`, `adr-path`, `close` and `release`. `plugin/scripts/exit.py` does not exist. (R3)
- [ ] `CLOSE.md` tells the agent to write `[close]` tags. A test checks it. (R4)
- [ ] `grep -rnw -e exit -e EXIT plugin tests evals/promptfoo evals/*.py README.md` shows no stage, skill or script name. Only exit codes, `sys.exit` and `## Exit criteria` stay. (R5)
- [ ] A test upgrades a repo with an unedited `.kairyn/stages/EXIT.md`. The file, its `.base/` copy and its manifest entry are gone, and the output has `REMOVED .kairyn/stages/EXIT.md`. (R6)
- [ ] A test upgrades a repo with an edited `EXIT.md`. The file stays, the output has `CONFLICT .kairyn/stages/EXIT.md` and the move-edits line, and the exit code is 1. (R7)
- [ ] A test deletes that file and upgrades again. The output has `REMOVED`, and the manifest has the new version. (R8)
- [ ] A test upgrades a repo whose recorded `EXIT.md` is missing. The output has `REMOVED`, and the `.base/` copy is gone. (R9)
- [ ] A test upgrades a repo with an unrecorded file at a no-longer-shipped path. The file stays. (R10)
- [ ] `uv run pytest` and `claude plugin validate plugin` pass. (R1, R2, R3, R5)

## Open questions and answers
- Q1: Which names clash? A: Only `exit`, the confirmed one. (D1, Jayson De los Reyes)
- Q2: What is the new name? A: `close`. (D2, Jayson De los Reyes)
- Q3: How far does the rename go? A: All that is shipped or tested. History stays. (D3, Jayson De los Reyes)
- Q4: What does upgrade do with the old file? A: A general removal step. (D4, Jayson De los Reyes)
- Q5: Do subcommands change? A: No. (D5, Jayson De los Reyes)

Approval: Jayson De los Reyes, 2026-11-24T23:18:20Z, "Yes, approved."
