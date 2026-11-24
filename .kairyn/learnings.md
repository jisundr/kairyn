# Learnings

Stages append here.
- 2026-11-24T23:17:06Z [grill] upgrade.py has no step that removes files a new plugin version stops shipping; any rename of a shipped file needs one. (2026-11-25-skill-names-clash)
- 2026-11-24T23:18:00Z [requirements] Old eval pass records in evals/results/passed.json are keyed by eval name; a renamed eval needs a fresh pass. (2026-11-25-skill-names-clash)
- 2026-11-24T23:20:19Z [design] Upgrade tests that cover a removed shipped file must install from a plugin copy that still ships it, so they stay valid after the file leaves plugin/. (2026-11-25-skill-names-clash)
