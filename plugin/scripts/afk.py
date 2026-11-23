#!/usr/bin/env python3
"""The AFK loop: runs the build, gates and review stages of a task with no user turns.

    python3 afk.py run <task>                       # run from the stage in STATE.md until a stop
    python3 afk.py approve <task> --words "<words>" # record the merge decision: approve
    python3 afk.py reject <task> --words "<reason>" # record the merge decision: reject

All take --root (default: the current directory). The script owns what must always work:
order, checks, git and STATE.md. The model only runs stage files, one `claude -p` per
slice `T<n>` and per stage, each with a fresh context.

  - Worktree: <git common dir>/kairyn/worktrees/<task>, branch kairyn/<task>. STATE.md there is the truth.
  - build: one session per T<n> of DESIGN.md, in `after:` order. Each T<n> needs a test(T<n>)
    commit whose done command fails (red) and a feat(T<n>) commit where it exits 0 (green).
    BUILD.md gets the SHAs and exit codes.
  - gates: each command in .kairyn/afk.yml `gates:`, in order. The exit code decides. An empty
    command is `not set`, never a pass. GATES.md gets one row per gate.
  - review: one session writes REVIEW.md with `Decision: pending`. The run then stops for the human.
A failed check sets `status: blocked` and logs why. Running `run` again resumes at `stage:`.
KAIRYN_CLAUDE overrides the claude binary (tests use a stub).

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

PLUGIN = Path(__file__).resolve().parent.parent
AFK_STAGES = ("build", "gates", "review")
MODELS = {"build": "opus", "review": "opus"}
_TASK_LINE = re.compile(r"^- (T\d+):(.*)$", re.M)
_AFTER = re.compile(r"\bafter:\s*((?:T\d+\s*,?\s*)+)")
_DONE = re.compile(r"\bDone:\s*`([^`]+)`")
_DECISION_PENDING = re.compile(r"^Decision: pending\s*$", re.M)


class Task(NamedTuple):
    id: str
    after: tuple
    done: str


class Blocked(Exception):
    """A check failed: the run stops with `status: blocked` and this reason."""


# --- pure parts ---------------------------------------------------------------------------------


def task_graph(design: str) -> list:
    """The T<n> lines of DESIGN.md in dependency order. Ties keep the T<n> number order."""
    tasks = {}
    for tid, rest in _TASK_LINE.findall(design):
        done = _DONE.search(rest)
        if not done:
            raise ValueError(f"{tid} has no done command (Done: `<command>`)")
        after = _AFTER.search(rest)
        tasks[tid] = Task(tid, tuple(re.findall(r"T\d+", after.group(1))) if after else (), done.group(1))
    if not tasks:
        raise ValueError("DESIGN.md has no T<n> lines")
    order, left = [], sorted(tasks, key=lambda t: int(t[1:]))
    while left:
        ready = [t for t in left if all(a in order or a not in tasks for a in tasks[t].after)]
        if not ready:
            raise ValueError(f"after: lines form a cycle: {', '.join(left)}")
        order.append(ready[0])
        left.remove(ready[0])
    return [tasks[t] for t in order]


def _value(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return int(raw) if re.fullmatch(r"-?\d+", raw) else raw


def _strip_comment(line: str) -> str:
    quote = None
    for i, ch in enumerate(line):
        if quote:
            quote = None if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i].rstrip()
    return line.rstrip()


def parse_afk(text: str) -> dict:
    """.kairyn/afk.yml: top-level `section:` keys, each holding `key: value` lines or `- item` lines."""
    data, section = {}, None
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if not line[0].isspace():
            key, sep, rest = line.partition(":")
            if not sep or rest.strip():
                raise ValueError(f"afk.yml: expected `section:`, got {raw!r}")
            section = key.strip()
            data[section] = None
            continue
        if section is None:
            raise ValueError(f"afk.yml: indented line before a section: {raw!r}")
        item = line.strip()
        if item.startswith("- "):
            data[section] = (data[section] or []) + [_value(item[2:])]
        else:
            key, sep, rest = item.partition(":")
            if not sep:
                raise ValueError(f"afk.yml: expected `key: value`, got {raw!r}")
            data[section] = {**(data[section] or {}), key.strip(): _value(rest) if rest.strip() else ""}
    return {k: (v if v is not None else {}) for k, v in data.items()}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def set_front(text: str, key: str, value: str, nested: bool = False) -> str:
    """Set `key: value` in STATE.md front matter. nested=True sets `  key: value` under `stages:`."""
    head, sep, body = text.partition("\n---\n")
    pattern = rf"^  {key}:.*$" if nested else rf"^{key}:.*$"
    line = f"  {key}: {value}" if nested else f"{key}: {value}"
    if re.search(pattern, head, re.M):
        head = re.sub(pattern, line, head, count=1, flags=re.M)
    elif nested:
        head = re.sub(r"^(stages:\n(?:  .*\n?)*)", lambda m: m.group(1).rstrip("\n") + "\n" + line + "\n", head,
                      count=1, flags=re.M).rstrip("\n")
    else:
        head += "\n" + line
    return head + sep + body


# --- the run ------------------------------------------------------------------------------------


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class Run:
    def __init__(self, root: Path, task: str):
        self.root, self.task = root, task
        common = Path(git(root, "rev-parse", "--git-common-dir"))
        self.common = common if common.is_absolute() else (root / common).resolve()
        self.wt = self.common / "kairyn" / "worktrees" / task
        self.branch = f"kairyn/{task}"

    @property
    def folder(self) -> Path:
        return self.wt / "docs" / "tasks" / self.task

    def ensure_worktree(self) -> None:
        if self.wt.is_dir():
            return
        self.wt.parent.mkdir(parents=True, exist_ok=True)
        exists = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--verify", "-q", self.branch],
                                capture_output=True).returncode == 0
        args = [str(self.wt), self.branch] if exists else ["-b", self.branch, str(self.wt)]
        git(self.root, "worktree", "add", "-q", *args)

    # STATE.md
    def state(self) -> str:
        return (self.folder / "STATE.md").read_text()

    def front(self, key: str) -> str | None:
        m = re.search(rf"^{key}:\s*([\w-]+)", self.state(), re.M)
        return m.group(1) if m else None

    def update(self, at: str, log: str, **fields: str) -> None:
        """Set front matter fields (stage_status=... sets stages.<stage>), bump `updated`, append a log line."""
        text = self.state()
        for key, value in fields.items():
            if key == "stage_status":
                text = set_front(text, at, value, nested=True)
            else:
                text = set_front(text, key, value)
        stamp = now()
        text = set_front(text, "updated", stamp)
        text = text.rstrip("\n") + f"\n{stamp} [{at}] {log}\n"
        (self.folder / "STATE.md").write_text(text)

    def commit(self, message: str) -> None:
        git(self.wt, "add", "-A", f"docs/tasks/{self.task}")
        if (self.wt / ".kairyn" / "learnings.md").is_file():
            git(self.wt, "add", ".kairyn/learnings.md")
        if subprocess.run(["git", "-C", str(self.wt), "diff", "--cached", "--quiet"]).returncode:
            git(self.wt, "commit", "-q", "-m", message)

    def claude(self, stage: str, prompt: str) -> str:
        binary = os.environ.get("KAIRYN_CLAUDE", "claude")
        cmd = [binary, "-p", prompt, "--model", MODELS.get(stage, "sonnet"), "--permission-mode", "bypassPermissions"]
        result = subprocess.run(cmd, cwd=self.wt, capture_output=True, text=True)
        if result.returncode:
            raise Blocked(f"claude exited {result.returncode}: {(result.stderr or result.stdout).strip()[-300:]}")
        return result.stdout.strip()

    def run_at(self, sha: str, command: str) -> int:
        """Exit code of `command` in a detached checkout of `sha`."""
        check = self.common / "kairyn" / "check" / self.task
        if check.exists():
            subprocess.run(["git", "-C", str(self.root), "worktree", "remove", "--force", str(check)], capture_output=True)
            shutil.rmtree(check, ignore_errors=True)
        check.parent.mkdir(parents=True, exist_ok=True)
        git(self.root, "worktree", "add", "-q", "--detach", str(check), sha)
        try:
            return subprocess.run(command, shell=True, cwd=check, capture_output=True).returncode
        finally:
            subprocess.run(["git", "-C", str(self.root), "worktree", "remove", "--force", str(check)], capture_output=True)

    def template(self, name: str) -> str:
        return (PLUGIN / "templates" / name).read_text().replace("<YYYY-MM-DD>-<slug>", self.task)

    # stages
    def build(self) -> None:
        path = self.folder / "BUILD.md"
        if not path.exists():
            path.write_text(self.template("BUILD.md"))
        try:
            graph = task_graph((self.folder / "DESIGN.md").read_text())
        except (OSError, ValueError) as e:
            raise Blocked(f"DESIGN.md: {e}")
        self.update("build", "Build started.", stage_status="in-progress")
        for t in graph:
            if re.search(rf"^\| {t.id} \|.*\| 0 \|\s*$", path.read_text(), re.M):
                continue   # green in an earlier run
            said = self.claude("build", f"Follow .kairyn/stages/BUILD.md for docs/tasks/{self.task}, task {t.id}. "
                                 f"Done command: `{t.done}`.")
            subjects = git(self.wt, "log", "--format=%h %s", "-n", "50").splitlines()
            test = next((s.split()[0] for s in subjects if s.split(" ", 1)[1].startswith(f"test({t.id})")), None)
            feat = next((s.split()[0] for s in subjects if s.split(" ", 1)[1].startswith(f"feat({t.id})")), None)
            if not test or not feat:
                raise Blocked(f"{t.id}: no test({t.id}) and feat({t.id}) commits. Session said: {said[-300:]}")
            red = self.run_at(test, t.done)
            if red == 0:
                raise Blocked(f"{t.id}: red check passed at {test}: the test did not fail before the code")
            green = self.run_at(feat, t.done)
            if green:
                raise Blocked(f"{t.id}: green check exited {green} at {feat}")
            path.write_text(path.read_text().rstrip("\n") + f"\n| {t.id} | {test} | {red} | {feat} | {green} |\n")
            self.commit(f"kairyn({self.task}): build {t.id} evidence")
        self.update("build", f"All {len(graph)} tasks green. Next: gates.", stage_status="done", stage="gates")

    def gates(self) -> None:
        config = self.wt / ".kairyn" / "afk.yml"
        if not config.is_file():
            raise Blocked("no .kairyn/afk.yml with a gates: list")
        gates = parse_afk(config.read_text()).get("gates") or {}
        path = self.folder / "GATES.md"
        rows = []
        try:
            for name, command in gates.items():
                if not command:
                    rows.append(f"| {name} | not set | - |")
                    continue
                code = subprocess.run(str(command), shell=True, cwd=self.wt, capture_output=True).returncode
                rows.append(f"| {name} | {'pass' if code == 0 else 'fail'} | {code} |")
                if code:
                    raise Blocked(f"gate {name} failed: `{command}` exited {code}")
        finally:
            path.write_text(self.template("GATES.md").rstrip("\n") + "\n" + "\n".join(rows) + "\n")
        self.update("gates", f"{len(rows)} gates run. Next: review.", stage_status="done", stage="review")

    def review(self) -> None:
        self.update("review", "Review started.", stage_status="in-progress")
        base = git(self.wt, "merge-base", "HEAD", git(self.root, "rev-parse", "HEAD"))
        self.claude("review", f"Follow .kairyn/stages/REVIEW.md for docs/tasks/{self.task}. "
                              f"The change is `git diff {base[:12]}..HEAD`.")
        path = self.folder / "REVIEW.md"
        if not path.is_file() or not _DECISION_PENDING.search(path.read_text()):
            raise Blocked("review wrote no REVIEW.md with `Decision: pending`")
        self.update("review", f"Waiting for the merge decision: /kairyn:review {self.task} approve or reject.",
                    status="blocked")

    def run(self) -> int:
        self.ensure_worktree()
        while True:
            stage, status = self.front("stage"), self.front("status")
            if status != "in-progress" or stage not in AFK_STAGES:
                print(f"STOP: {self.task} is {status} at {stage}. Worktree: {self.wt}")
                return 0
            try:
                getattr(self, stage)()
            except Blocked as e:
                self.update(stage, f"Blocked: {e}", status="blocked")
                print(f"BLOCKED: {stage}: {e}")
            self.commit(f"kairyn({self.task}): {stage}")

    def decide(self, words: str, approve: bool) -> int:
        path = self.folder / "REVIEW.md"
        if not path.is_file() or not _DECISION_PENDING.search(path.read_text()):
            print(f"FAIL: {self.task} has no REVIEW.md with `Decision: pending`")
            return 1
        name = git(self.root, "config", "user.name")
        line = f'Decision: {name}, {now()}, "{words}"'
        path.write_text(_DECISION_PENDING.sub(line.replace("\\", "\\\\"), path.read_text(), count=1))
        if approve:
            self.update("review", f"Approved by {name}.", stage_status="done", status="done")
        else:
            self.update("review", f"Rejected by {name}: {words}", status="blocked")
        self.commit(f"kairyn({self.task}): decision")
        print(line)
        return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("run", "approve", "reject"))
    parser.add_argument("task")
    parser.add_argument("--words", default="")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if "/" in args.task or not (args.root / "docs" / "tasks" / args.task).is_dir():
        print(f"FAIL: no task folder docs/tasks/{args.task}/")
        return 1
    run = Run(args.root.resolve(), args.task)
    if args.command == "run":
        return run.run()
    if not args.words:
        print("FAIL: --words is required")
        return 1
    return run.decide(args.words, args.command == "approve")


if __name__ == "__main__":
    sys.exit(main())
