---
task: 2026-11-25-skill-names-clash
stage: grill
summary: "Rename the exit stage to close so a bare /exit no longer quits the session; upgrade removes files it no longer ships."
---

# Concept: Skill names clash with built-in commands

## Concept
A bare `/exit` runs the Claude Code built-in and quits the session, not the kairyn stage. Kairyn renames the `exit` stage to `close`; `init` and `review` keep their names. The rename covers all that the plugin ships or tests: skill, `CLOSE.md`, `close.py` with the same subcommands, `[close]` log tag, harness docs, budgets, eval and tests. History stays as written. `/kairyn:upgrade` gets a removal step: it deletes an unedited `EXIT.md` (`REMOVED`) or keeps an edited copy and reports `CONFLICT`.

## Decisions
- D1: Rename only the `exit` skill and stage. A bare `/exit` runs the built-in and quits the session. `init` and `review` stay as they are. (user accepted)
- D2: The new name is `close`. The stage docs already use that verb. (user accepted)
- D3: Rename everything the plugin ships or tests: skill, `CLOSE.md`, `close.py`, `[close]` log tag, harness docs, budgets, eval and tests. History stays as written: `CHANGELOG.md`, old task logs, past eval results. (user)
- D4: `upgrade.py` gets a general removal step for files the new version no longer ships. An unedited copy is deleted with its `.base/` copy and reported `REMOVED`. An edited copy stays and is reported `CONFLICT`, with a line that tells the user to move edits into `CLOSE.md`. (user accepted)
- D5: `close.py` keeps its subcommands: `check`, `adr-path`, `close`, `release`. Only the file name changes. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| clash | A kairyn skill name equals a Claude Code built-in command name. |
| removal step | The `upgrade.py` step that removes files the new plugin version no longer ships. |

## Open branches
- None
