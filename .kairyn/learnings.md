# Learnings

Stages append here.
- 2026-11-26 [close] After a plugin version bump, run `python3 plugin/scripts/upgrade.py --root .` in this repo. `test_dev_harness.py` fails until `.kairyn/manifest.json` has the new version.
- 2026-11-26 [close] Build adds no `CHANGELOG.md` line: `close.py close --entry` writes it after the merge.
- 2026-11-26 [close] Run `plugin/scripts/budgets.py` before an eval: a cut to a file over its budget makes the eval pass stale, and the eval runs again.
- 2026-11-26 [close] The close skill names the installed plugin's `close.py`, which can predate this repo's. In this repo, run `plugin/scripts/close.py`.
- 2026-11-28 [build] Grill rounds can cover every open branch before a scripted stop. A multi-turn grill eval must accept an early restatement, not count question turns.
- 2026-11-28 [review] Ban `git diff main` in Test plan commands with a lint rule or gate because a stale local `main` makes the check fail or pass for reasons outside the change; use `origin/main` or the merge base.
