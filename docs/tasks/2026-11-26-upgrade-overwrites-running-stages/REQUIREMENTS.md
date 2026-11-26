---
task: 2026-11-26-upgrade-overwrites-running-stages
stage: requirements
summary: "Remove this repo's note from the plugin-owned running-stages.md; upgrade.py prints a SAVED line for each .kairyn-old."
---

# Requirements: Upgrade overwrites this repo's edited running-stages.md

## Problem statement
Each upgrade replaces this repo's `.harness/workflows/running-stages.md` with the shipped copy. The doc is plugin-owned, so this is correct. But the repo had one edit in it: the `union` note in step 3. Workers restored the note by hand three times (PR #48, #50, #54). When `upgrade.py` saves an edited copy to `<file>.kairyn-old`, it prints only `REPLACED <file>` and exits 0. A person who runs the script directly gets no sign that an edit was moved aside.

## Scope
In: remove the `union` note from this repo's `running-stages.md`. (D1, D3)
In: `upgrade.py` prints a `SAVED` line for each `.kairyn-old` it writes. (D1, D2)
In: the `upgrade` harness doc names the `SAVED` line. (repo rule: change a workflow, update its doc)
Out: init ships the `.gitattributes` union line to every repo. It is the inbox idea `20261126064130-init-ships-union-merge`. (D4)
Out: a new exit code for `SAVED`. (D2)
Out: an ignore rule for `.kairyn-old` files.

## Requirements
- R1: When `upgrade.py` saves an edited plugin-owned file to `<file>.kairyn-old`, the script shall print one line that starts `SAVED <file>.kairyn-old`. (D1, D2)
- R2: The `SAVED` line shall tell the user the next step: move the edits into a file the repo owns, then delete the `.kairyn-old` file. (D2)
- R3: If `upgrade.py` replaces a plugin-owned file and writes no `.kairyn-old`, the script shall print no `SAVED` line. (D2)
- R4: The script shall return the same exit code with a `SAVED` line as without one. (D2)
- R5: The `union` note shall be only in the `.gitattributes` comment. This repo's `running-stages.md` shall be the same as the shipped copy. (D3)
- R6: The `upgrade` harness doc shall name the `SAVED` line in its rules. (repo rule)

## Non-functional needs
- Accessibility: not applicable: CLI text only.
- Performance: not applicable: no source states a need.
- Security: not applicable: no new input or file path.
- Observability: the `SAVED` line is the change. (R1)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | The `/kairyn:upgrade` command text stays as it is. Step 2 already reports every result line, and step 4 already names each `.kairyn-old`. So no instruction changes and no eval is needed. | design |
| A2 | assumption | The plugin version goes up by one patch or minor step, and `release_hashes.py --write` runs. | design |
| A3 | assumption | For the `CLAUDE.md` block, the `SAVED` line names `CLAUDE.md.kairyn-old`, the file the script writes. | design |
| K1 | risk | The parallel task also bumps the plugin version. If its PR merges first, this branch rebases and takes the next version. | build |

## Acceptance criteria
- [ ] A test upgrades a repo with an edited plugin-owned file. The output has `SAVED <file>.kairyn-old` and the next step, and the exit code is 0. (R1, R2, R4)
- [ ] A test upgrades a repo with an unedited plugin-owned file that the plugin changed. The output has `REPLACED` and no `SAVED` line. (R3)
- [ ] `diff plugin/harness/.harness/workflows/running-stages.md .harness/workflows/running-stages.md` prints nothing, and `.gitattributes` keeps its comment. (R5)
- [ ] `.harness/workflows/upgrade.md` names the `SAVED` line, and `uv run pytest` passes. (R6)

## Open questions and answers
- None.

Approval: Jayson De los Reyes, 2026-11-26T07:00:31Z, "Approve"
