# Learnings

Stages append here.
- 2026-11-24T23:17:06Z [grill] upgrade.py has no step that removes files a new plugin version stops shipping; any rename of a shipped file needs one. (2026-11-25-skill-names-clash)
- 2026-11-24T23:18:00Z [requirements] Old eval pass records in evals/results/passed.json are keyed by eval name; a renamed eval needs a fresh pass. (2026-11-25-skill-names-clash)
- 2026-11-24T23:20:19Z [design] Upgrade tests that cover a removed shipped file must install from a plugin copy that still ships it, so they stay valid after the file leaves plugin/. (2026-11-25-skill-names-clash)
- 2026-11-25T00:06:28Z [review] Ban upgrade.py from deleting an edited file without a .base/ copy with a test, because the stored local bytes become the base and the next run deletes the edits. (2026-11-25-skill-names-clash)
- 2026-11-25T00:06:28Z [review] Ban a merge of a plugin/ change without a passing eval summary.md with a gate, because K1 evals (close, upgrade) had no run in the change. (2026-11-25-skill-names-clash)
- 2026-11-25T00:06:28Z [review] Ban new `# noqa` in evals/promptfoo/ with a lint rule, because feat(T3) added two escape hatches no reviewer justified. (2026-11-25-skill-names-clash)
- 2026-11-25 [close] Commit the task folder on the kairyn/<task> branch before /kairyn:build: afk.py builds the worktree from HEAD, and its start check also needs docs/tasks/<task>/ in the main checkout. (2026-11-25-skill-names-clash)
- 2026-11-25 [close] afk.py does not resume a task with status: blocked; after the fix, set status: in-progress in STATE.md and log why. (2026-11-25-skill-names-clash)
- 2026-11-25 [grill] For a pain the user names from another repo, read that repo's Claude session transcript (~/.claude/projects/<repo>): its user turns gave counts the draft problem had wrong. (2026-11-25-first-mate-hub)
- 2026-11-25 [requirements] afk.py writes every STATE.md log line through one method, `update()`: a feature that mirrors run progress hooks in there. (2026-11-25-first-mate-hub)
- 2026-11-25 [design] Claude Code's Monitor tool sends each stdout line of a command as a chat message (30 min max, then re-arm): use it for watchers that must report more than once. (2026-11-25-first-mate-hub)
- 2026-11-25T02:35:13Z [review] Ban a merge of a criterion that needs a real session with no recorded run, with a gate, because AC13 (0 "status?" asks) stays unproven after merge. (2026-11-25-first-mate-hub)
- 2026-11-25T02:35:13Z [review] Ban hook events and files outside DESIGN.md with a gate, because PostToolUseFailure and 5 files went in unrecorded. (2026-11-25-first-mate-hub)
- 2026-11-25T02:35:13Z [review] Ban test edits in a fix round with no new red run, with a gate, because the red commits no longer prove tests/test_milestones.py. (2026-11-25-first-mate-hub)
- 2026-11-25T03:35:53Z [review] Ban hook payload fixtures with no script that records them again, with a gate, because a change in the Claude Code payload shape breaks return_code in milestones.py with no failing test. (2026-11-25-first-mate-hub)
- 2026-11-25T03:35:53Z [review] Ban test or fixture changes in a feat commit with a lint rule, because d4c5daf changed tests/fixtures/hooks/ in the green step. (2026-11-25-first-mate-hub)
