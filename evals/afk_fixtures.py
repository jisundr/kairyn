"""Fixtures and runs for the AFK stage evals (build, gates, review). afk.py drives each run.

The repo is a small `textstats.py` CLI. The task adds `--lines` (AC1). The review fixture also
asks for `--chars` (AC2), which the branch does not build, so a correct review names it.
Gates and review start from a ready kairyn/<task> branch, so only the stage under test spends tokens.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from helpers import PLUGIN, ROOT, make_good_repo
from runner import new_repo, utcnow

AFK = PLUGIN / "scripts" / "afk.py"
WRAPPER = ROOT / "evals" / "afk_claude.py"
AFK_TASK = "2026-01-05-line-count"
APPROVED = 'Approval: Eval User, 2026-01-05T09:20:00Z, "Approve"'

TEXTSTATS = '''"""Text statistics for the stats CLI: reads stdin, prints a number."""
import sys


def word_count(text):
    return len(text.split())


if __name__ == "__main__":
    print(word_count(sys.stdin.read()))
'''
TEXTSTATS_TEST = '''import unittest

from textstats import word_count


class WordCountTest(unittest.TestCase):
    def test_counts_words(self):
        self.assertEqual(word_count("a b  c"), 3)


if __name__ == "__main__":
    unittest.main()
'''
LINES_CODE = TEXTSTATS.replace('''if __name__ == "__main__":
    print(word_count(sys.stdin.read()))''', '''def line_count(text):
    return len(text.splitlines())


if __name__ == "__main__":
    data = sys.stdin.read()
    print(line_count(data) if "--lines" in sys.argv else word_count(data))  # noqa: E501''')
LINES_TEST = '''import subprocess
import sys
import unittest


class LinesTest(unittest.TestCase):
    def test_lines_flag_prints_the_line_count(self):
        out = subprocess.run([sys.executable, "textstats.py", "--lines"], input="a\\nb\\nc\\n",
                             capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "3")


if __name__ == "__main__":
    unittest.main()
'''

STATE = """---
task: {task}
title: Line count flag
stage: build
status: in-progress
stages:
  requirements: done
  design: done
  build: pending
  gates: pending
  review: pending
created: 2026-01-05T09:00:00Z
updated: 2026-01-05T09:20:00Z
---

# Log

2026-01-05T09:20:00Z [design] Approved by Eval User.
"""
REQUIREMENTS = """---
task: {task}
stage: requirements
summary: "A --lines flag{chars_summary}."
---

# Requirements: Line count flag

## Requirements
- R1: When `python3 textstats.py --lines` runs, the CLI shall print the number of lines read from stdin. (request)
{chars_req}
## Acceptance criteria
- [ ] `printf 'a\\nb\\nc\\n' | python3 textstats.py --lines` prints `3`. (R1)
{chars_ac}
{approved}
"""
CHARS_REQ = "- R2: When `python3 textstats.py --chars` runs, the CLI shall print the number of characters read from stdin. (request)\n"
CHARS_AC = "- [ ] `printf 'abc' | python3 textstats.py --chars` prints `3`. (R2)\n"
DESIGN = """---
task: {task}
stage: design
summary: "One slice: line_count() and the --lines flag."
---

# Design: Line count flag

## Approach
Option A. Add `line_count(text)` to `textstats.py` and read `--lines` from `sys.argv`.

## Tasks
- T1: Tracer bullet. `textstats.py --lines` prints the line count of stdin. Test in `test_lines.py` (new) runs the CLI. Done: `python3 -m unittest test_lines` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 prints the line count | T1 | `test_lines.py` |

{approved}
"""
AFK_YML = """limits:
  build_usd: 4
  gates_usd: 1
  review_usd: {review_usd}
  run_usd: 6
  stage_minutes: 20
gates:
  testing: python3 -m unittest -q
{extra_gates}  security:
{checks}"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def make_afk_repo(parent: Path, *, review_usd: float = 0, extra_gates: str = "", checks: str = "",
                  chars: bool = False) -> Path:
    """A kairyn repo with the textstats CLI and an approved one-slice design. review_usd 0 stops the run before review."""
    repo = make_good_repo(new_repo(parent, "repo"))
    for k, v in (("user.name", "Eval User"), ("user.email", "eval@example.com")):
        git(repo, "config", k, v)
    (repo / "textstats.py").write_text(TEXTSTATS)
    (repo / "test_textstats.py").write_text(TEXTSTATS_TEST)
    task = repo / "docs" / "tasks" / AFK_TASK
    task.mkdir(parents=True)
    (task / "STATE.md").write_text(STATE.format(task=AFK_TASK))
    (task / "REQUIREMENTS.md").write_text(REQUIREMENTS.format(
        task=AFK_TASK, approved=APPROVED, chars_summary=" and a --chars flag" if chars else "",
        chars_req=CHARS_REQ if chars else "", chars_ac=CHARS_AC if chars else ""))
    (task / "DESIGN.md").write_text(DESIGN.format(task=AFK_TASK, approved=APPROVED))
    (repo / ".kairyn" / "afk.yml").write_text(AFK_YML.format(review_usd=review_usd, extra_gates=extra_gates,
                                                             checks=checks))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def make_built_branch(repo: Path, stage: str) -> None:
    """kairyn/<task> with T1 built (one escape hatch flagged) and STATE.md at `stage`. main stays at the base."""
    git(repo, "checkout", "-q", "-b", f"kairyn/{AFK_TASK}")
    (repo / "test_lines.py").write_text(LINES_TEST)
    git(repo, "add", "test_lines.py")
    git(repo, "commit", "-q", "-m", "test(T1): --lines prints the line count")
    test_sha = git(repo, "rev-parse", "--short", "HEAD").strip()
    (repo / "textstats.py").write_text(LINES_CODE)
    git(repo, "commit", "-qam", "feat(T1): add line_count and --lines")
    feat_sha = git(repo, "rev-parse", "--short", "HEAD").strip()
    task = repo / "docs" / "tasks" / AFK_TASK
    build = (PLUGIN / "templates" / "BUILD.md").read_text().replace("<YYYY-MM-DD>-<slug>", AFK_TASK)
    noqa = next(i for i, line in enumerate(LINES_CODE.splitlines(), 1) if "# noqa" in line)
    build = build.rstrip("\n") + f"\n| T1 | {test_sha} | 1 | {feat_sha} | 0 |\n\n## Flags\n" \
        f"- escape hatch: `textstats.py:{noqa}` `# noqa` in feat(T1)\n\n## Review\n- Review 1: Findings: none\n"
    (task / "BUILD.md").write_text(build)
    state = (task / "STATE.md").read_text().replace("stage: build", f"stage: {stage}").replace(
        "  build: pending", "  build: done")
    if stage == "review":
        state = state.replace("  gates: pending", "  gates: done")
        gates = (PLUGIN / "templates" / "GATES.md").read_text().replace("<YYYY-MM-DD>-<slug>", AFK_TASK)
        (task / "GATES.md").write_text(gates.rstrip("\n") + "\n| testing | pass | 0 | - |\n| security | not set | - | - |\n")
    (task / "STATE.md").write_text(state + "2026-01-05T10:00:00Z [build] All 1 tasks green. Next: gates.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"kairyn({AFK_TASK}): build")
    git(repo, "checkout", "-q", "main")


def run_afk(repo: Path, run_dir: Path) -> dict:
    """One `afk.py run` with the real claude behind the wrapper. Returns what the asserts read."""
    start = utcnow()
    env = {**os.environ, "KAIRYN_CLAUDE": str(WRAPPER), "AFK_EVAL_DIR": str(run_dir)}
    proc = subprocess.run([sys.executable, str(AFK), "run", AFK_TASK, "--root", str(repo)], capture_output=True,
                          text=True, env=env, timeout=3600)
    wt = repo / ".git" / "kairyn" / "worktrees" / AFK_TASK
    folder = wt / "docs" / "tasks" / AFK_TASK

    def read(path: Path) -> str:
        return path.read_text() if path.is_file() else ""

    base = git(repo, "rev-parse", "main").strip()
    commits = git(wt, "log", "--reverse", "--format=%h %s", f"{base}..HEAD").splitlines() if wt.is_dir() else []
    sessions = []
    for path in sorted(run_dir.glob("session-*.jsonl"), key=lambda p: int(p.stem.split("-")[1])):
        prompt = read(path.with_suffix(".prompt.txt"))
        events = [json.loads(line) for line in path.read_text().splitlines() if line.startswith("{")]
        sessions.append({"prompt": prompt, "events": events})
    return {"stdout": proc.stdout, "exit": proc.returncode, "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "task_path": str(folder),
            "state": read(folder / "STATE.md"), "build": read(folder / "BUILD.md"), "gates": read(folder / "GATES.md"),
            "review": read(folder / "REVIEW.md"), "commits": commits,
            "learnings_before": read(repo / ".kairyn" / "learnings.md"),
            "learnings": read(wt / ".kairyn" / "learnings.md"),
            "test_textstats_changed": bool(wt.is_dir() and git(wt, "diff", base, "HEAD", "--", "test_textstats.py")),
            "sessions": sessions}
