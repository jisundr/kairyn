---
description: Upgrade this repo's kairyn files to the installed plugin version, keeping your edits
allowed-tools: Bash(python3:*), Read
---

Upgrade kairyn in the current repository. The script does the work; do not edit or merge files by hand.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/upgrade.py --root .` from the repo root.
2. Report every result line exactly (`REPLACED`, `MERGED`, `ADDED`, `CONFLICT`, `KEPT`).
3. For each `CONFLICT`, tell the user: the local file is unchanged and the merge is in `<file>.kairyn-new`. They take what they want from it, delete it, and run `/kairyn:upgrade` again.
4. Name any `<file>.kairyn-old` it wrote: the user's edited copy of a replaced kairyn file.
