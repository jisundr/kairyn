---
name: backlog
order: 30
optional: true
purpose: Hold the idea rules. Run it to save, triage or commit ideas.
---

# Stage: backlog

An idea is `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md`, named from its UTC capture time.

- Front matter: `title`, `status`, `requester`, `date`, `effort`, `impact`, `review_by`.
- Status: `inbox` → `triaged` → `committed`, or `parked` (until `review_by`) or `dropped`.
- `effort` (work) and `impact` (value) are each `low`, `medium` or `high`.
- Each change is a line under `# Log`: timestamp, tag (`[capture]`, `[triage]`, `[commit]`), who.
- AI captures and proposes. A human triages, confirms and commits.

## Inputs
- The request, or the ideas in `docs/backlog/`.

## Steps
Capture:
1. Draft a slug, title and one or two sentence problem. Propose effort, impact.
2. From the repo root, run once: `python3 <plugin>/scripts/backlog.py capture --slug --title --effort --impact --request --problem`. `--request` is the user's words, unchanged. Add `--requester` only for another named person.

Triage, from the repo root:
1. Run `python3 <plugin>/scripts/backlog.py digest`. Read each one.
2. For each, propose keep, park or drop with one reason, and effort and impact. Stop and wait for the owner.
3. For each decided idea, run `python3 <plugin>/scripts/backlog.py decide <file> keep|park|renew|drop --reason`. Keep adds `--effort --impact`; park and renew (a parked idea) add `--by`, the owner's date. No date: ask.
4. When the owner commits a triaged idea, run `python3 <plugin>/scripts/backlog.py commit <file>` and show the commands it prints.

## Output
Capture never overwrites. Triage sets status and a `[triage]` line. Commit sets `committed`, a `[commit]` line and the task's `STATE.md`. `docs/backlog/README.md` lists only triaged ideas.

## Exit criteria
- [ ] Capture: one new `inbox` idea.
- [ ] No idea changed without the owner's decision.
- [ ] Each `FAIL:` line is reported.

## State update
Only commit creates one.

## Learnings
None.
