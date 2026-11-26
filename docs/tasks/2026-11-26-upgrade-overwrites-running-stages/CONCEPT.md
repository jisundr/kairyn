---
task: 2026-11-26-upgrade-overwrites-running-stages
stage: grill
summary: "Stop upgrades from silently dropping this repo's union note in running-stages.md."
---

# Concept: Upgrade overwrites this repo's edited running-stages.md

## Concept
This repo stops editing the plugin-owned `.harness/workflows/running-stages.md`: the union note is removed from step 3, and it stays only in the `.gitattributes` comment. Then an upgrade replaces the doc with no loss. `upgrade.py` also prints one `SAVED <file>.kairyn-old` line for each edited plugin-owned file that it saves before a replace, with what the user does next. The exit code stays 0, as for `REPLACED`. "Init ships the union merge for every repo" is a separate inbox idea, not in this batch.

## Decisions
- D1: Fix both ways: remove the note from the plugin-owned doc, and make upgrade print a warning for each `.kairyn-old`. (user accepted)
- D2: The warning is one extra line, `SAVED <file>.kairyn-old`, with the next step. The exit code stays 0. (user accepted)
- D3: The union note stays only in the `.gitattributes` comment. It goes out of `running-stages.md`. (user accepted)
- D4: Capture "init ships the learnings.md union merge for every repo" as a new inbox idea, outside this batch. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| plugin-owned file | A file that upgrade always replaces (`kairyn_files.owner_of` returns `plugin`). |
| `.kairyn-old` | The copy of an edited plugin-owned file that upgrade saves before it replaces the file. |
| union note | Step 3's note in `running-stages.md` that `.gitattributes` merges `learnings.md` by `union`. |

## Open branches
- None.

Approval: Jayson De los Reyes, 2026-11-26T06:44:29Z, "Approve"
