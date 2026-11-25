# 16. Upgrade removes files a release no longer ships

Date: 2026-11-25

## Status
Accepted

## Context
Task 2026-11-25-skill-names-clash renamed the `exit` stage to `close`, because a bare `/exit` runs the Claude Code built-in and quits the session. `upgrade.py` had no step that removes a file. After the rename, consumer repos kept `.kairyn/stages/EXIT.md` next to `CLOSE.md`. Two options were possible: (A) a general removal step, the user moves edits by hand, (B) a shipped rename map that merges an edited old file into the new file. Option B adds a file format, and a wrong merge can move edits silently.

## Decision
Option A. After the shipped-file loop, `upgrade.py` checks each path that `.kairyn/manifest.json` records and the plugin no longer ships. An unedited copy (it matches its `.base/` copy or a released hash) is deleted with its `.base/` copy and manifest entry, and upgrade prints `REMOVED`. An edited copy stays, upgrade prints `CONFLICT` and tells the user to move the edits and delete the file. A missing copy is `REMOVED`. A file the manifest does not record is never deleted. A record with no real `.base/` copy is marked `no_base`, and only the user's delete removes that file.

## Consequences
- A future rename of a shipped file needs no special upgrade code.
- The manifest takes the new version only when the user deleted each edited old file.
- Upgrade tests for a removed file install from a plugin copy that still ships it.
- The `no_base` rule came from review finding F1: without it, the second upgrade deleted the user's edits.
