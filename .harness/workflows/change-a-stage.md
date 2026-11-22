---
title: Change a stage
summary: "Eval-first loop for editing a stage, the stage file format and adding a new stage."
read_when: "editing or adding a stage in plugin/stages/"
load: on-demand
---

# Change a stage

Stage files in `plugin/stages/` are instructions for the model, so changing them is probabilistic work. Use the eval-first loop.

## Edit an existing stage

1. **Write or tighten the eval first.** Add the scenario that describes the behavior you want, in the stage's `evals/promptfoo/<name>.yaml`.
2. **Watch it fail** on the current instructions (`uv run python evals/run.py <name> --all-evals`). An eval that has never failed has not proven anything.
3. **Edit the stage** until it passes at the full run count.
4. **Read the evidence** in `evals/results/<run-id>/`, not only the pass line.
5. Run `uv run pytest` and `claude plugin validate plugin`.

Lessons already learned, so you do not repeat them:
- State what to do in every case. "Advance `stage`" failed 3 of 10 runs because the only stage had nothing to advance to. The fix spells out three cases (next stage, last stage, blocked).
- Do not let the model invent facts it cannot know. Timestamps and dates come from `date`.
- Check the checker. A bad check (YAML turning timestamps into datetimes) produced a false 0 of 10. Pure checks live in `evals/checks.py` with tests.

## Stage file format

Copy `plugin/stages/_template.md`. Required front matter: `name` (the lowercase stage name, matching the filename case-insensitively), `order` (unique integer), `purpose`. Required sections: Inputs, Steps, Output, Exit criteria, State update, Learnings. `tests/test_static.py` enforces this.

Stage files and their outputs are upper case (`REQUIREMENTS.md`). Stage names and `STATE.md` values are lower case (`requirements`).

## Add a new stage

1. Write its eval first (`evals/promptfoo/<name>.yaml` with a `# depends:` header on the stage file, `_template.md` and `templates/STATE.md`).
2. Create the stage file from `_template.md` with the next `order`.
3. Add the stage to `stages:` in `plugin/templates/STATE.md`, and update the previous stage's State update so it advances to the new one.
4. Make sure `init.sh` needs no change: it copies everything in `plugin/stages/` and `plugin/templates/`.
5. Update the README layout.

## Optional stages

A stage that only some tasks need (for example `model-routing`) sets `optional: true` in its front matter. Do not add it to `stages:` in `STATE.md`, and do not make the previous stage advance to it. Its State update adds the stage to the task's `stages` when it runs. Give it an `order` above the main stages.
