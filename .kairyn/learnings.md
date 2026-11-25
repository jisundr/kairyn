# Learnings

Stages append here.
- 2026-11-24T23:17:06Z [grill] upgrade.py has no step that removes files a new plugin version stops shipping; any rename of a shipped file needs one. (2026-11-25-skill-names-clash)
- 2026-11-24T23:18:00Z [requirements] Old eval pass records in evals/results/passed.json are keyed by eval name; a renamed eval needs a fresh pass. (2026-11-25-skill-names-clash)
- 2026-11-24T23:20:19Z [design] Upgrade tests that cover a removed shipped file must install from a plugin copy that still ships it, so they stay valid after the file leaves plugin/. (2026-11-25-skill-names-clash)
- 2026-11-25T00:06:28Z [review] Ban upgrade.py from deleting an edited file without a .base/ copy with a test, because the stored local bytes become the base and the next run deletes the edits. (2026-11-25-skill-names-clash)
- 2026-11-25T00:06:28Z [review] Ban a merge of a plugin/ change without a passing eval summary.md with a gate, because K1 evals (close, upgrade) had no run in the change. (2026-11-25-skill-names-clash)
- 2026-11-25T00:06:28Z [review] Ban new `# noqa` in evals/promptfoo/ with a lint rule, because feat(T3) added two escape hatches no reviewer justified. (2026-11-25-skill-names-clash)
