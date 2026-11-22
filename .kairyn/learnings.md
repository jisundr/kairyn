# Learnings

Stages append here.

- 2026-11-22 [requirements] This repo installs its own plugin, so its dev harness and the consumer harness share `CLAUDE.md`, `.harness/README.md` and `budgets.yml`. Only one `harness-docs` marker pair may exist in a file (`harness_docs.py` updates the first). Keep kairyn's own `CLAUDE.md` text under budget so the plugin block fits.
- 2026-11-22 [requirements] requirements is the only stage, so finishing it marks the task `done` even though design and build are still to do. A design stage is the next gap.
- 2026-11-22 [design] `verify-init.sh` also byte-compares installed stages with the plugin, so it fails as soon as a user edits a stage. The design's default mode drops that compare for repo-owned files.
- 2026-11-22 [build] This repo's `.harness/README.md`, `budgets.yml` and `task-lifecycle.md` are dev docs at consumer paths. Upgrade reports them as conflicts once; delete each `.kairyn-new` to keep ours.
- 2026-11-22 [build] `/kairyn:check write` rewrites the doc index in the CLAUDE.md block, so the block's hash leaves the index out. Otherwise every check would make upgrade see an edit.
- 2026-11-22 [build] Headless `claude -p --permission-mode acceptEdits` refuses Bash beyond simple read-only commands: a globbed `grep` "requires approval". Stage steps that must work in evals use Read and Glob, not shell pipelines.
- 2026-11-22 [build] On macOS the filesystem ignores case: `GRILL.md` and `grill.md` in one folder are the same file. Draft stage and command files in separate folders.
