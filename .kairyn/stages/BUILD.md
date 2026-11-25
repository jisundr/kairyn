---
name: build
order: 3
purpose: Build one slice T<n> of an approved DESIGN.md test-first, in two commits that afk.py checks.
---

# Stage: build

`afk.py` runs this stage twice per `T<n>`, each time in a fresh session with no user. The prompt names the task, the `T<n>`, its done command and the part. The tests part does steps 1-3 only. The code part does steps 4-6 only, from the `test(T<n>)` commit, and changes no test file.

## Inputs
- The task's `REQUIREMENTS.md` and `DESIGN.md`: the `T<n>` line and the criteria it serves.
- `BUILD.md`: the slices that are green. `.kairyn/learnings.md`.

## Steps
1. Read the `T<n>` line and the code it names. Do only that `T<n>`.
2. Write the test for `T<n>` only. Run the done command. It must fail because the code is missing.
3. Commit only the test: `test(T<n>): <what it checks>`.
4. Write the least code that makes the test pass. Run the done command and the full test suite.
5. Read the error output before each new edit. Stop after 3 failed attempts.
6. Commit the code: `feat(T<n>): <what it does>`.

Never edit, skip or weaken a test from step 3 to get exit 0. Never add a lint suppression to get exit 0.

A fix round prompt lists reviewer findings instead of a `T<n>`. Fix them in one `fix: <what>` commit, and keep every test.

## Output
Two commits on the task branch. Change no file in `docs/tasks/`: `afk.py` owns them.

## Exit criteria
- [ ] The done command fails at the `test(T<n>)` commit and exits 0 at the `feat(T<n>)` commit.

If 3 attempts fail, or the `T<n>` line is wrong, make no `feat(T<n>)` commit. End with one line that says why. `afk.py` blocks the task with it.

## State update
None. `afk.py` checks both commits, writes `BUILD.md` and updates `STATE.md`.

## Learnings
None in this stage. `review` writes them.
