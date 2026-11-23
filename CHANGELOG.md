# Changelog

## Unreleased

- The requirements stage writes EARS requirements, non-functional needs and risks with owners, and waits for your approval in chat. (2026-11-22-requirements-gaps)
- New optional grill stage, /kairyn:grill: Claude interviews you one question at a time and writes CONCEPT.md, which requirements reads. (2026-11-22-grill-me)
- /kairyn:upgrade brings installed kairyn files to a new plugin version and keeps your edits with a three-way merge. A session-start hook says when to run it. (2026-11-22-plugin-versioning)
- Built-in stages run as skills with their own model: grill and model-routing on Sonnet, requirements on Opus. Eval summaries show cost per run. (2026-11-22-stage-skills)
- New optional exit stage, /kairyn:exit: it writes ADRs, a changelog line and learnings for a done task, then deletes the task folder and closed backlog files. (2026-11-22-exit-strategy)
- New required design stage, /kairyn:design: Claude proposes options, writes DESIGN.md with tasks and a test plan, and waits for approval in chat. (2026-11-23-design-stage)
- The shared writing rule now bans hedge words such as `would` in stage outputs, even when quoted from your request. (2026-11-23-eval-request-hedge)
- Contributors run evals with /run-evals: a background subagent runs them and returns a short report with failures, evidence and cost. (2026-11-23-eval-subagent)
