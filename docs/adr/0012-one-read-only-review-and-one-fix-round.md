# 12. One read-only review and one fix round, then escalate

Date: 2026-11-24

## Status
Accepted

## Context
Task 2026-11-23-build-stage. Build had to check the change against its requirements before the pull request, with no user turns (D2, D3). A test edit or a lint suppression can make a check pass with no real fix (D12, D19).

## Decision
- After every slice passes, a reviewer session with read-only tools reads the diff against `REQUIREMENTS.md` and `DESIGN.md` (D3).
- `afk.py` flags a later edit to a test-commit file and each added line that matches `escape_hatches:` (D12, D19). The reviewer asks to remove or justify each flag.
- Findings get one fix round. If a test still fails or the reviewer still objects, the run escalates (D3, D5).
- Open findings and accepted escape hatches go to `.kairyn/learnings.md` as constraints. Retro sends a fix to agent-written code to the backlog as a lint rule or gate (D20).

## Consequences
- A real run with a finding found three defects that the stub tests did not. The fix round now clears that finding.
- A flag does not block the run. The human sees what is left in `REVIEW.md`.
