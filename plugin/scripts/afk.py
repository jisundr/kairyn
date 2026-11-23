#!/usr/bin/env python3
"""The AFK loop: runs the build, gates and review stages of a task with no user turns.

    python3 afk.py run <task>                       # run from the stage in STATE.md until a stop
    python3 afk.py approve <task> --words "<words>" # record the merge decision: approve
    python3 afk.py reject <task> --words "<reason>" # record the merge decision: reject
    python3 afk.py approve <task> --slice T<n> --words "<words>"  # approve one (approval) slice

All take --root (default: the current directory). The script owns what must always work:
order, checks, git and STATE.md. The model only runs stage files, one `claude -p` per
slice `T<n>` and per stage, each with a fresh context.

  - Worktree: <git common dir>/kairyn/worktrees/<task>, branch kairyn/<task>. STATE.md there is the truth.
  - build: one session per T<n> of DESIGN.md, in `after:` order. Each T<n> needs a test(T<n>)
    commit whose done command fails (red) and a feat(T<n>) commit where it exits 0 (green).
    BUILD.md gets the SHAs and exit codes. Then the script lists flags (a later commit that edits a
    test file, an added line that matches `escape_hatches:`), and a read-only reviewer session reads
    the diff. Findings get one fix round. If a finding stays or a done command fails, the run blocks.
  - gates: each command in .kairyn/afk.yml `gates:`, in order, security last. The exit code decides.
    An empty command is `not set`, never a pass. A gate with a `checks:` entry then gets a read-only
    session that prints PASS or FAIL: <why>. GATES.md gets one row per gate.
  - review: one session writes REVIEW.md with `Decision: pending`. The run then stops for the human.
A failed check sets `status: blocked` and logs why. Running `run` again resumes at `stage:`.
Readiness (before the first stage): the `testing` gate has a command, each set gate exits 0 on the
base commit, and the worktree has no tracked changes. Limits (afk.yml `limits:`, else DEFAULT_LIMITS):
a cost cap per stage and per run, from each session's `total_cost_usd`, and minutes per stage. A limit
blocks the run with the limit, the cost so far and the last failed command.
Approval gates: build stops before a slice marked `(approval)` in DESIGN.md until BUILD.md has
`Approval T<n>: ...`. Before gates and review, each changed path that matches afk.yml `approval:`
needs an approval of the slice that changed it.
Publish: with an `origin` remote, each stage ends with a push of kairyn/<task>. Build then opens one
pull request with gh, review posts REVIEW.md on it, and approve merges it with a merge commit. With no
remote or no gh, the run logs that and goes on; approve then only records the decision.
A repo with no .kairyn/afk.yml gets one from the template, and the run stops so a person sets it.
KAIRYN_GH overrides the gh binary (tests use a stub).
KAIRYN_CLAUDE overrides the claude binary (tests use a stub).

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import fnmatch
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
MODELS = {"build": "opus", "reviewer": "opus", "gate": "sonnet", "review": "opus"}
DEFAULT_ESCAPES = ["# noqa", "# type: ignore", "eslint-disable", "@ts-ignore", "@ts-expect-error",
                   r"pytest\.mark\.skip", r"\.skip\(", r"\bxit\("]
DEFAULT_LIMITS = {"build_usd": 10, "gates_usd": 5, "review_usd": 3, "run_usd": 20, "stage_minutes": 60}
READ_ONLY = ["--disallowedTools", "Edit,Write,NotebookEdit",
             "--allowedTools", "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)"]
_TASK_LINE = re.compile(r"^- (T\d+):(.*)$", re.M)
_AFTER = re.compile(r"\bafter:\s*((?:T\d+\s*,?\s*)+)")
_DONE = re.compile(r"\bDone:\s*`([^`]+)`")
_DECISION_PENDING = re.compile(r"^Decision: pending\s*$", re.M)


class Task(NamedTuple):
    id: str
    after: tuple
    done: str
    approval: bool = False


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
        tasks[tid] = Task(tid, tuple(re.findall(r"T\d+", after.group(1))) if after else (), done.group(1),
                          "(approval)" in rest)
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
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return float(raw) if re.fullmatch(r"-?\d*\.\d+", raw) else raw


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


def path_matches(path: str, pattern: str) -> bool:
    """A glob where `**/` at the start also matches no folder: `**/migrations/**` matches `migrations/x.sql`."""
    return fnmatch.fnmatch(path, pattern) or (pattern.startswith("**/") and fnmatch.fnmatch(path, pattern[3:]))


def add_row(text: str, row: str) -> str:
    """Put a row after the last table line of BUILD.md (its only table)."""
    lines = text.rstrip("\n").split("\n")
    last = max(i for i, line in enumerate(lines) if line.startswith("|"))
    return "\n".join(lines[:last + 1] + [row] + lines[last + 1:]) + "\n"


def escape_patterns(config: dict) -> list:
    """The `escape_hatches:` regex list of afk.yml, or the defaults when it has none."""
    return list(config.get("escape_hatches") or DEFAULT_ESCAPES)


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
        self.rounds = []
        self.run_cost, self.stage_cost, self.stage_name, self.stage_start = 0.0, 0.0, "", 0.0
        self.last_failed = "none"

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

    def limits(self) -> dict:
        return {**DEFAULT_LIMITS, **(self.config().get("limits") or {})}

    def start_stage(self, name: str) -> None:
        import time
        self.stage_name, self.stage_cost, self.stage_start = name, 0.0, time.monotonic()

    def limit_hit(self, what: str) -> Blocked:
        return Blocked(f"limit {what} reached: spent ${self.stage_cost:.2f} in {self.stage_name}, "
                       f"${self.run_cost:.2f} in this run. Last failed command: {self.last_failed}")

    def seconds_left(self) -> float:
        import time
        minutes = self.limits()["stage_minutes"]
        left = minutes * 60 - (time.monotonic() - self.stage_start)
        if left <= 0:
            raise Blocked(f"limit stage_minutes {minutes} reached in {self.stage_name}. "
                          f"Last failed command: {self.last_failed}")
        return left

    def check_cost(self) -> None:
        limits = self.limits()
        stage_cap = limits.get(f"{self.stage_name}_usd")
        if stage_cap is not None and self.stage_cost >= stage_cap:
            raise self.limit_hit(f"{self.stage_name}_usd ${stage_cap}")
        if self.run_cost >= limits["run_usd"]:
            raise self.limit_hit(f"run_usd ${limits['run_usd']}")

    def claude(self, stage: str, prompt: str, read_only: bool = False) -> str:
        import json
        self.check_cost()
        limits = self.limits()
        budget = min(limits.get(f"{self.stage_name}_usd", limits["run_usd"]) - self.stage_cost,
                     limits["run_usd"] - self.run_cost)
        binary = os.environ.get("KAIRYN_CLAUDE", "claude")
        cmd = [binary, "-p", prompt, "--model", MODELS.get(stage, "sonnet"), "--output-format", "json",
               "--max-budget-usd", f"{budget:.2f}"]
        cmd += READ_ONLY if read_only else ["--permission-mode", "bypassPermissions"]
        try:
            result = subprocess.run(cmd, cwd=self.wt, capture_output=True, text=True, timeout=self.seconds_left())
        except subprocess.TimeoutExpired:
            raise Blocked(f"limit stage_minutes {limits['stage_minutes']} reached in {self.stage_name}. "
                          f"Last failed command: {self.last_failed}")
        try:
            data = json.loads(result.stdout)
        except ValueError:
            data = {"result": result.stdout}
        text, cost = str(data.get("result") or ""), float(data.get("total_cost_usd") or 0)
        self.stage_cost += cost
        self.run_cost += cost
        errors = "; ".join(data.get("errors") or [])
        if data.get("subtype") == "error_max_budget_usd":
            cap = f"{self.stage_name}_usd ${limits[f'{self.stage_name}_usd']}" if f"{self.stage_name}_usd" in limits \
                else f"run_usd ${limits['run_usd']}"
            raise Blocked(f"limit {cap} reached in a session: {errors}. Spent ${self.stage_cost:.2f} in "
                          f"{self.stage_name}, ${self.run_cost:.2f} in this run. Last failed command: {self.last_failed}")
        if result.returncode:
            raise Blocked(f"claude exited {result.returncode}: {(errors or result.stderr or text).strip()[-300:]}")
        return text.strip()

    def command(self, command: str, cwd: Path, label: str) -> int:
        """Run a check command; remember it when it fails."""
        try:
            result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True,
                                    timeout=self.seconds_left())
        except subprocess.TimeoutExpired:
            raise Blocked(f"limit stage_minutes {self.limits()['stage_minutes']} reached in {self.stage_name}. "
                          f"Last failed command: `{command}` {label}")
        if result.returncode:
            out = " ".join((result.stderr or result.stdout).split())[-200:]
            self.last_failed = f"`{command}` exit {result.returncode} {label}: {out}"
        return result.returncode

    def run_at(self, sha: str, command: str, label: str) -> int:
        """Exit code of `command` in a detached checkout of `sha`."""
        check = self.common / "kairyn" / "check" / self.task
        if check.exists():
            subprocess.run(["git", "-C", str(self.root), "worktree", "remove", "--force", str(check)], capture_output=True)
            shutil.rmtree(check, ignore_errors=True)
        check.parent.mkdir(parents=True, exist_ok=True)
        git(self.root, "worktree", "add", "-q", "--detach", str(check), sha)
        try:
            return self.command(command, check, label)
        finally:
            subprocess.run(["git", "-C", str(self.root), "worktree", "remove", "--force", str(check)], capture_output=True)

    def config(self) -> dict:
        path = self.wt / ".kairyn" / "afk.yml"
        return parse_afk(path.read_text()) if path.is_file() else {}

    def base(self) -> str:
        return git(self.wt, "merge-base", "HEAD", git(self.root, "rev-parse", "HEAD"))

    def flags(self) -> list:
        """Lines for BUILD.md: test files that a later commit edits, and added lines that match an escape hatch."""
        commits = git(self.wt, "log", "--reverse", "--format=%h %s", f"{self.base()}..HEAD").splitlines()
        patterns = [re.compile(p) for p in escape_patterns(self.config())]
        tests, found = set(), []
        for sha, subject in (c.split(" ", 1) for c in commits):
            label = subject.split(":", 1)[0]
            if label.startswith("kairyn("):
                continue
            files = git(self.wt, "show", "--name-only", "--format=", sha).splitlines()
            if label.startswith("test("):
                tests.update(files)
                continue
            found += [f"test edit: `{f}` in {label}" for f in files if f in tests]
            name, line = None, 0
            for diff_line in git(self.wt, "show", "-U0", "--format=", sha).splitlines():
                if diff_line.startswith("+++ "):
                    name = diff_line[6:] if diff_line.startswith("+++ b/") else None
                elif diff_line.startswith("@@"):
                    line = int(re.search(r"\+(\d+)", diff_line).group(1))
                elif diff_line.startswith("+") and name:
                    hit = next((m for m in (p.search(diff_line[1:]) for p in patterns) if m), None)
                    if hit:
                        found.append(f"escape hatch: `{name}:{line}` `{hit.group(0)}` in {label}")
                    line += 1
        return found

    def reviewer(self, flags: list) -> list:
        listed = "\n".join(f"- {f}" for f in flags) or "- none"
        said = self.claude("reviewer", (
            f"You are the reviewer for docs/tasks/{self.task}. Read its REQUIREMENTS.md and DESIGN.md and "
            f"`git diff {self.base()[:12]}..HEAD`. Change nothing. Report each acceptance criterion with no test, "
            "each change outside DESIGN.md, each test that checks nothing, and each flag below with no good reason. "
            "Print one line per finding as `FINDING: <text>`, or `FINDINGS: none`.\nFlags:\n" + listed), read_only=True)
        return [line.split(":", 1)[1].strip() for line in said.splitlines() if line.startswith("FINDING:")]

    def write_sections(self, path: Path, flags: list, findings: list, round_: str) -> None:
        text = path.read_text().split("\n## Flags\n", 1)[0].rstrip("\n")   # keeps ## Approvals
        text += "\n\n## Flags\n" + ("\n".join(f"- {f}" for f in flags) or "- None") + "\n"
        self.rounds.append(f"- {round_}: " + ("; ".join(findings) if findings else "Findings: none"))
        text += "\n## Review\n" + "\n".join(self.rounds) + "\n"
        path.write_text(text)

    def approved(self, tid: str) -> bool:
        path = self.folder / "BUILD.md"
        return path.is_file() and bool(re.search(rf'^Approval {tid}: .+, \d{{4}}-[\d-]+T[\d:]+Z, ".+"$',
                                                  path.read_text(), re.M))

    def backstop(self) -> None:
        """D10: each changed path that matches `approval:` needs an approval of the slice that changed it."""
        patterns = self.config().get("approval") or []
        if not patterns:
            return
        commits = git(self.wt, "log", "--reverse", "--format=%h %s", f"{self.base()}..HEAD").splitlines()
        for sha, subject in (c.split(" ", 1) for c in commits):
            label = subject.split(":", 1)[0]
            if label.startswith("kairyn("):
                continue
            tid = re.search(r"T\d+", label)
            ok = self.approved(tid.group(0)) if tid else bool(re.search(r"^Approval T\d+: ", (
                self.folder / "BUILD.md").read_text(), re.M))
            for name in git(self.wt, "show", "--name-only", "--format=", sha).splitlines():
                pattern = next((p for p in patterns if path_matches(name, str(p))), None)
                if pattern and not ok:
                    who = tid.group(0) if tid else "T<n>"
                    raise Blocked(f"approval: `{name}` matches `{pattern}` in {label} with no approval. Run "
                                  f"/kairyn:build {self.task} approve {who} \"<words>\"")

    def approve_slice(self, tid: str, words: str) -> int:
        path = self.folder / "BUILD.md"
        try:
            ids = [t.id for t in task_graph((self.folder / "DESIGN.md").read_text())]
        except (OSError, ValueError):
            ids = []
        if tid not in ids or not path.is_file():
            print(f"FAIL: {tid} is not a slice of {self.task} with a BUILD.md")
            return 1
        name = git(self.root, "config", "user.name")
        line = f'Approval {tid}: {name}, {now()}, "{words}"'
        text = path.read_text()
        if "\n## Approvals\n" not in text:
            head, sep, rest = text.partition("\n## Flags\n")
            text = head.rstrip("\n") + "\n\n## Approvals\n" + (("\n" + sep.lstrip("\n") + rest) if sep else "")
        head, _, rest = text.partition("\n## Approvals\n")
        section, sep, tail = rest.partition("\n## ")
        text = head + "\n## Approvals\n" + section.rstrip("\n") + ("\n" if section.strip() else "") + line + "\n" + \
            (("\n## " + tail) if sep else "")
        path.write_text(text)
        self.update(self.front("stage"), f"{tid} approved by {name}: {words}", status="in-progress")
        self.commit(f"kairyn({self.task}): approve {tid}")
        print(line)
        return 0

    def review_loop(self, graph: list, path: Path) -> None:
        """D3: a read-only reviewer, one fix round, then escalation."""
        flags = self.flags()
        findings = self.reviewer(flags)
        self.write_sections(path, flags, findings, "Review 1")
        self.commit(f"kairyn({self.task}): review 1")
        if not findings:
            return
        self.claude("build", f"Follow .kairyn/stages/BUILD.md for docs/tasks/{self.task}, fix round. "
                             "Fix these review findings, keep every test, and commit as `fix: <what>`:\n"
                             + "\n".join(f"- {f}" for f in findings))
        for t in graph:
            code = self.command(t.done, self.wt, "after the fix round")
            if code:
                raise Blocked(f"{t.id}: done command exited {code} after the fix round")
        flags = self.flags()
        findings = self.reviewer(flags)
        self.write_sections(path, flags, findings, "Review 2, after the fix round")
        self.commit(f"kairyn({self.task}): review 2")
        if findings:
            raise Blocked("the reviewer still objects after the fix round: " + "; ".join(findings))

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
            if t.approval and not self.approved(t.id):
                raise Blocked(f"{t.id} is marked (approval). Read it in DESIGN.md, then run "
                              f"/kairyn:build {self.task} approve {t.id} \"<words>\"")
            said = self.claude("build", f"Follow .kairyn/stages/BUILD.md for docs/tasks/{self.task}, task {t.id}. "
                                 f"Done command: `{t.done}`.")
            subjects = git(self.wt, "log", "--format=%h %s", "-n", "50").splitlines()
            test = next((s.split()[0] for s in subjects if s.split(" ", 1)[1].startswith(f"test({t.id})")), None)
            feat = next((s.split()[0] for s in subjects if s.split(" ", 1)[1].startswith(f"feat({t.id})")), None)
            if not test or not feat:
                raise Blocked(f"{t.id}: no test({t.id}) and feat({t.id}) commits. Session said: {said[-300:]}")
            red = self.run_at(test, t.done, "at the red check")
            if red == 0:
                raise Blocked(f"{t.id}: red check passed at {test}: the test did not fail before the code")
            green = self.run_at(feat, t.done, "at the green check")
            if green:
                raise Blocked(f"{t.id}: green check exited {green} at {feat}")
            path.write_text(add_row(path.read_text(), f"| {t.id} | {test} | {red} | {feat} | {green} |"))
            self.commit(f"kairyn({self.task}): build {t.id} evidence")
            self.check_cost()
        self.review_loop(graph, path)
        self.check_cost()
        self.update("build", f"All {len(graph)} tasks green. Cost ${self.stage_cost:.2f}. Next: gates.",
                    stage_status="done", stage="gates")

    def gate_check(self, name: str, check: str) -> str:
        """An inferential check inside a gate (D9): '' when it passes, else the reason."""
        said = self.claude("gate", (
            f"You run the {name} gate check for docs/tasks/{self.task}. Follow .kairyn/stages/GATES.md. "
            f"Read `git diff {self.base()[:12]}..HEAD` and change nothing. Check: {check}\n"
            "Print `PASS`, or `FAIL: <one-line reason>`."), read_only=True)
        last = next((line for line in reversed(said.splitlines()) if line.startswith(("PASS", "FAIL"))), "")
        if last.startswith("PASS"):
            return ""
        return last[5:].strip() if last.startswith("FAIL:") else f"no PASS or FAIL line: {said[-120:]}"

    def gates(self) -> None:
        if not (self.wt / ".kairyn" / "afk.yml").is_file():
            raise Blocked("no .kairyn/afk.yml with a gates: list")
        gates = self.config().get("gates") or {}
        checks = self.config().get("checks") or {}
        path = self.folder / "GATES.md"
        rows = []
        try:
            for name, command in gates.items():
                if not command:
                    rows.append(f"| {name} | not set | - | - |")
                    continue
                code = self.command(str(command), self.wt, f"at gate {name}")
                if code:
                    rows.append(f"| {name} | fail | {code} | - |")
                    raise Blocked(f"gate {name} failed: `{command}` exited {code}")
                why = self.gate_check(name, str(checks[name])) if checks.get(name) else None
                rows.append(f"| {name} | {'fail' if why else 'pass'} | 0 | "
                            f"{'-' if why is None else 'check: ' + (why or 'pass')} |")
                if why:
                    raise Blocked(f"gate {name} check failed: {why}")
        finally:
            path.write_text(self.template("GATES.md").rstrip("\n") + "\n" + "\n".join(rows) + "\n")
        unset = [n for n, c in gates.items() if not c]
        note = f"{len(gates) - len(unset)} pass, {len(unset)} not set" + (f": {', '.join(unset)}" if unset else "")
        self.update("gates", f"{note}. Cost ${self.stage_cost:.2f}. Next: review.", stage_status="done", stage="review")

    def review(self) -> None:
        self.update("review", "Review started.", stage_status="in-progress")
        base = self.base()
        self.claude("review", f"Follow .kairyn/stages/REVIEW.md for docs/tasks/{self.task}. "
                              f"The change is `git diff {base[:12]}..HEAD`.")
        path = self.folder / "REVIEW.md"
        if not path.is_file() or not _DECISION_PENDING.search(path.read_text()):
            raise Blocked("review wrote no REVIEW.md with `Decision: pending`")
        self.check_cost()
        self.update("review", f"Cost ${self.stage_cost:.2f}. Waiting for the merge decision: /kairyn:review {self.task} approve or reject.",
                    status="blocked")

    def readiness(self) -> None:
        """D18: before the first stage. Untracked files (build output such as __pycache__/) do not count."""
        out = subprocess.run(["git", "-C", str(self.wt), "status", "--porcelain", "--untracked-files=no"],
                             check=True, capture_output=True, text=True).stdout
        own = f"docs/tasks/{self.task}/"   # a person edits STATE.md to resume: that is not a change to the code
        names = ", ".join(n for n in (line[3:] for line in out.splitlines()) if not n.startswith(own))
        if names:
            raise Blocked(f"readiness: the worktree has changes: {names}")
        if self.front("stage") != "build" or (self.folder / "BUILD.md").exists():
            return   # gates on the base commit run once, before the first build
        gates = self.config().get("gates") or {}
        if "security" in gates and list(gates)[-1] != "security":
            raise Blocked("readiness: the security gate must be last in .kairyn/afk.yml, so it checks the final code")
        if not gates.get("testing"):
            raise Blocked("readiness: the testing gate in .kairyn/afk.yml has no command")
        for name, command in gates.items():
            if command:
                code = self.command(str(command), self.wt, f"at gate {name} on the base commit")
                if code:
                    raise Blocked(f"readiness: gate {name} exits {code} on the base commit")

    # publish
    def gh(self) -> str | None:
        path = os.environ.get("KAIRYN_GH")
        if path:
            return path if Path(path).is_file() else None
        return shutil.which("gh")

    def has_remote(self) -> bool:
        return "origin" in git(self.root, "remote").split()

    def pr_exists(self, gh: str) -> bool:
        return subprocess.run([gh, "pr", "view", self.branch, "--json", "url"], cwd=self.root,
                              capture_output=True).returncode == 0

    def push(self) -> None:
        result = subprocess.run(["git", "-C", str(self.wt), "push", "-q", "-u", "origin", self.branch],
                                capture_output=True, text=True)
        if result.returncode:
            raise Blocked(f"git push failed: {' '.join(result.stderr.split())[-200:]}")

    def publish(self, done: str) -> None:
        """After a stage commit: push; after build, open the pull request; after review, post REVIEW.md."""
        built = done == "build" and self.front("stage") == "gates"
        if not self.has_remote():
            if built:
                self.update("build", "No remote: no push and no pull request.")
                self.commit(f"kairyn({self.task}): no remote")
            return
        self.push()
        gh = self.gh()
        if built:
            if not gh:
                self.update("build", f"Pushed {self.branch}. No gh: no pull request.")
            elif not self.pr_exists(gh):
                base = git(self.root, "symbolic-ref", "--short", "HEAD")
                title = re.search(r"^title:\s*(.+)$", self.state(), re.M)
                result = subprocess.run([gh, "pr", "create", "--base", base, "--head", self.branch, "--title",
                                         title.group(1) if title else self.task, "--body-file",
                                         str(self.folder / "BUILD.md")], cwd=self.root, capture_output=True, text=True)
                if result.returncode:
                    raise Blocked(f"gh pr create failed: {' '.join(result.stderr.split())[-200:]}")
                self.update("build", f"Pushed {self.branch}. Pull request: {result.stdout.strip()}")
            self.commit(f"kairyn({self.task}): pull request")
            self.push()
        if done == "review" and gh and _DECISION_PENDING.search((self.folder / "REVIEW.md").read_text() if (
                self.folder / "REVIEW.md").is_file() else "") and self.pr_exists(gh):
            subprocess.run([gh, "pr", "comment", self.branch, "--body-file", str(self.folder / "REVIEW.md")],
                           cwd=self.root, capture_output=True)

    def ensure_config(self) -> bool:
        """A repo set up before afk.yml existed gets it from the template. False: a person must set it first."""
        target = self.root / ".kairyn" / "afk.yml"
        if target.is_file():
            return True
        source = self.root / ".kairyn" / "templates" / "afk.yml"
        shutil.copyfile(source if source.is_file() else PLUGIN / "templates" / "afk.yml", target)
        print("BLOCKED: Created .kairyn/afk.yml. Set the testing gate command, commit the file, then run again.")
        return False

    def run(self) -> int:
        if not self.ensure_config():
            return 1
        self.ensure_worktree()
        self.start_stage(self.front("stage") or "")
        if self.front("status") == "in-progress":
            try:
                self.readiness()
            except Blocked as e:
                self.update(self.front("stage"), f"Blocked: {e}", status="blocked")
                print(f"BLOCKED: {e}")
                self.commit(f"kairyn({self.task}): readiness")
        while True:
            stage, status = self.front("stage"), self.front("status")
            if status != "in-progress" or stage not in AFK_STAGES:
                print(f"STOP: {self.task} is {status} at {stage}. Worktree: {self.wt}")
                return 0
            self.start_stage(stage)
            try:
                if stage != "build":
                    self.backstop()
                getattr(self, stage)()
            except Blocked as e:
                self.update(stage, f"Blocked: {e}", status="blocked")
                print(f"BLOCKED: {stage}: {e}")
            self.commit(f"kairyn({self.task}): {stage}")
            try:
                self.publish(stage)
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
        if not approve:
            self.update("review", f"Rejected by {name}: {words}", status="blocked")
            self.commit(f"kairyn({self.task}): decision")
            print(line)
            return 0
        self.update("review", f"Approved by {name}.", stage_status="done", status="done")
        self.commit(f"kairyn({self.task}): decision")
        print(line)
        gh = self.gh()
        if not self.has_remote():
            return 0
        try:
            self.push()
            if gh and self.pr_exists(gh):
                result = subprocess.run([gh, "pr", "merge", self.branch, "--merge"], cwd=self.root,
                                        capture_output=True, text=True)
                if result.returncode:
                    raise Blocked(f"gh pr merge failed: {' '.join((result.stderr or result.stdout).split())[-200:]}")
                self.update("review", "Merged with gh pr merge --merge.")
            else:
                self.update("review", f"Pushed {self.branch}. No pull request to merge: merge it by hand.")
        except Blocked as e:
            self.update("review", f"Blocked: {e}", status="blocked")
            self.commit(f"kairyn({self.task}): merge")
            print(f"FAIL: {e}")
            return 1
        self.commit(f"kairyn({self.task}): merge")
        return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("run", "approve", "reject"))
    parser.add_argument("task")
    parser.add_argument("--words", default="")
    parser.add_argument("--slice", default="", help="approve one (approval) slice T<n>, not the merge")
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
    if args.slice:
        if args.command != "approve":
            print("FAIL: --slice works only with approve")
            return 1
        return run.approve_slice(args.slice, args.words)
    return run.decide(args.words, args.command == "approve")


if __name__ == "__main__":
    sys.exit(main())
