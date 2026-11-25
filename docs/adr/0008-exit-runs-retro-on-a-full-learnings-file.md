# 8. Exit runs retro when learnings.md passes half its budget

Date: 2026-11-23

## Status
Accepted. Amended by [ADR 19](0019-opus-decides-cheaper-models-carry-out.md): close and retro stay on Sonnet, as retro failed on Haiku (K1).

## Context
Task 2026-11-23-retro-stage. Every stage appends to `.kairyn/learnings.md`, and nothing removed an entry. This repo's file was at 994 of 1000 tokens, and stages could not append. The user does not need to remember a retro (D5). `EXIT.md` was at 469 of 500 tokens, and exit has no approval gate. Whether one skill can start another on the right model is unproven (K2).

## Decision
- Retro is a separate optional stage with a `/kairyn:retro` skill (D1, D6).
- `exit.py close` prints a `RETRO:` line past half the budget. Exit then follows `RETRO.md` in the same turn. No skill starts another skill (design option A).
- A script, `retro.py`, does each size and owner check: `size`, and `fits` with `FITS`, `OVER <n>`, `KAIRYN-OWNED` or `MISSING`.
- Each run has its own task folder and waits for approval before it changes a file (D2, D9).
- A move goes only into a file the repo owns or kairyn never touches (D7). Tests, scripts, kairyn-owned files, files that `CLAUDE.md` guards and full homes become backlog ideas (D3, D8, D10). Retro never raises a budget.

## Consequences
- Retro from exit runs on the exit model (Sonnet). The exit eval passed `exit_starts_retro` 10/10.
- In this repo, most learnings about evals become backlog ideas while `testing-and-evals.md` is full.
- `RETRO.md` is at its 500-token budget. A new rule must replace text.
