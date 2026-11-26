# Learnings

Stages append here.
- 2026-11-25 [close] A phone-width need gets a test that measures page width in a browser: the owner found a 507 px page at 390 px that the HTML tests passed (2026-11-25-backlog-page).
- 2026-11-26 [close] A skill moves to a cheaper model only after its eval passes there at 10 runs: retro failed on Haiku (5/10, 7/10) while close passed (2026-11-26-split-build-routing).
- 2026-11-26 [close] A split into more sessions can cost more, not less: the two-session afk_build eval cost $7.45 against $4.67 all on Opus (2026-11-26-split-build-routing).
- 2026-11-26 [close] A task built by hand has no REVIEW.md, so close.py check fails: record the merge in STATE.md (status done) and copy the owner's merge into a REVIEW.md Decision line (2026-11-26-close-changelog-double-name).
- 2026-11-26 [build] Headless Chrome keeps a minimum window width (about 500 px), so a --window-size=390 screenshot is cropped: load the page in a 390 px iframe and crop the shot (2026-11-26-effort-and-impact).
- 2026-11-26 [close] A fixed list order is not a sort control: the owner asked for "sorting" and rejected a page with only a default order, so offer a visible Sort select (2026-11-26-effort-and-impact).
- 2026-11-26 [build] plugin/scripts/upgrade.py takes no flags: `--help` runs the upgrade, which replaced the edited running-stages.md (kept as .kairyn-old). Restore it from git (2026-11-26-ship-evals-gate).
- 2026-11-26 [close] Closing a task merged by hand needs no edits by hand: close step 1 runs close.py record-merge, which writes STATE.md and REVIEW.md from the merged PR. This replaces the 2026-11-26 rule above about a hand-written REVIEW.md (2026-11-26-close-hand-merged).
- 2026-11-26 [build] An edit to a plugin-owned file in this repo (`.harness/workflows/` docs from `plugin/harness/`, templates, the CLAUDE.md block) is lost on each upgrade. Put the note in a file the repo owns; upgrade now prints `SAVED <file>.kairyn-old` when it moves an edit aside (2026-11-26-upgrade-overwrites-running-stages).
