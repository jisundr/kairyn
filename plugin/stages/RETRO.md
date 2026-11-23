---
name: retro
order: 95
optional: true
purpose: Give each learning one action, wait for approval, then apply it. Run it when learnings.md is past half its budget.
---

# Stage: retro

Optional: `/kairyn:retro` runs it, or exit on a `RETRO:` line. The skill names the script.

## Inputs
- `.kairyn/learnings.md`, the repo's `CLAUDE.md`, `.harness/` and `.kairyn/stages/`.

## Steps
1. Get timestamps from `date`. Create `docs/tasks/<date>-retro/` with a `STATE.md` whose `stages` holds only `retro: in-progress`. Run `size`.
2. Number entries `L1`, `L2`, … in file order. Read each `.harness/` doc's `read_when` and each stage's `purpose`. An entry's home is the file whose trigger matches it. `CLAUDE.md` only if every session needs it.
3. Give each entry one action:
   - drop: a file already holds the rule (name it), or the entry is stale.
   - backlog: the home is a test or a script, or `CLAUDE.md` asks for a step before the home changes.
   - move: run `fits <home> --add "<text>"`. `FITS`: move. `OVER <n>` or `KAIRYN-OWNED`: backlog, with that word. `MISSING`: choose again.
   - keep: no home fits yet. Say why.
4. Fill `.kairyn/templates/RETRO.md`. If kept entries use over half the budget, state the excess and ask.
5. Change no file outside the task folder. Ask for approval.
6. On approval, add each move's text to its home. Write one `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md` per backlog entry: `title`, `status: inbox`, `date`, the learning word for word. Remove each entry that is not kept. Never edit a kept entry or a budget.

## Output
`RETRO.md` in the task folder, in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] Each entry has one action, and the user approved.

## State update
As in `_template.md`. Until approval: `status: blocked`, `Approval: pending`. Other replies are not approval. On approval: `Approval: <git config user.name>, <timestamp>, "<the user's words>"`, `retro: done`, `status: done`.

## Learnings
None: retro empties `learnings.md`.
