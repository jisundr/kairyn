---
name: backlog
order: 30
optional: true
purpose: Hold the idea rules and capture one idea. Run it when the user has an idea to keep for later.
---

# Stage: backlog

An idea is one file, `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md`, named from its UTC capture time.

- Front matter: `title`, `status`, `requester`, `date`, `effort`, `impact`, `review_by`.
- Status: `inbox` → `triaged` → `committed`, or `parked` (until `review_by`) or `dropped`.
- `effort` (the work) and `impact` (the value) are each `low`, `medium` or `high`.
- Each change is a line under `# Log`: timestamp, tag (`[capture]`, `[triage]`, `[commit]`), who.
- AI captures, drafts and proposes. A human triages, confirms and commits.

## Inputs
- The user's request.

## Steps
1. Draft a slug, a title and the problem in one or two sentences. Propose effort and impact.
2. Run once, from the repo root: `python3 <plugin>/scripts/backlog.py capture --slug --title --effort --impact --request --problem`. `--request` is the user's words, unchanged. Add `--requester` only if the request names another person.

## Output
The idea file. The script also creates `docs/backlog/README.md` if missing, and never overwrites.

## Exit criteria
- [ ] One new idea file with `status: inbox`, or the script's `FAIL:` line reported.

## State update
None: no task exists yet.

## Learnings
None.
