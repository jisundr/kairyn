---
name: backlog
order: 30
optional: true
purpose: Hold the idea rules, capture one idea and triage ideas. Run it to save an idea or decide on ideas.
---

# Stage: backlog

An idea is one file, `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md`, named from its UTC capture time.

- Front matter: `title`, `status`, `requester`, `date`, `effort`, `impact`, `review_by`.
- Status: `inbox` → `triaged` → `committed`, or `parked` (until `review_by`) or `dropped`.
- `effort` (the work) and `impact` (the value) are each `low`, `medium` or `high`.
- Each change is a line under `# Log`: timestamp, tag (`[capture]`, `[triage]`, `[commit]`), who.
- AI captures, drafts and proposes. A human triages, confirms and commits.

## Inputs
- Capture: the user's request. Triage: the ideas in `docs/backlog/`.

## Steps
Capture:
1. Draft a slug, a title and the problem in one or two sentences. Propose effort and impact.
2. Run once, from the repo root: `python3 <plugin>/scripts/backlog.py capture --slug --title --effort --impact --request --problem`. `--request` is the user's words, unchanged. Add `--requester` only if the request names another person.

Triage, from the repo root:
1. Run `python3 <plugin>/scripts/backlog.py digest`. Read each idea it lists.
2. For each, propose keep, park or drop with one reason, and effort and impact. Stop and wait for the owner.
3. For each idea the owner decided, run `python3 <plugin>/scripts/backlog.py decide <file> keep|park|renew|drop --reason`. Keep adds `--effort --impact`; park and renew (a parked idea) add `--by`, the owner's date. No date: ask.

## Output
Capture: the idea file; it never overwrites. Triage: each decided idea gets its status and a `[triage]` line. `docs/backlog/README.md` lists only triaged ideas.

## Exit criteria
- [ ] Capture: one new idea file with `status: inbox`.
- [ ] Triage: no idea changed without the owner's decision.
- [ ] Each `FAIL:` line is reported.

## State update
None: no task exists yet.

## Learnings
None.
