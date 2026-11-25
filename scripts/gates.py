"""Review gates for this repo's AFK runs. `.kairyn/afk.yml` `gates:` runs each one as a command.

  design    each changed file and each new hook event is named in DESIGN.md
  commits   no feat commit changes a test or fixture; a fix-round edit of a test comes in a test commit that is red
  evals     after a plugin/ change, each eval that depends on a changed file has a pass at the current hash
  sessions  each `Manual` row of the DESIGN.md test plan has a `Run AC<n>: ...` line in a task file

Each gate reads the commits on the branch kairyn/<task> after its merge base with main. With no code
commits (readiness runs gates on the base commit) every gate passes. Exit 0 passes; exit 1 lists each problem.
"""
import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from selector import deps_hash, load_record, parse_depends

GREEN_PAIR = re.compile(r"(test|feat)\(T\d+\)")


def git(*args: str, cwd: Path = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode:
        raise SystemExit(f"FAIL: git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def is_test(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return bool({"tests", "test", "fixtures", "__tests__"} & set(parts[:-1])) or name.startswith("test_") or \
        bool(re.search(r"(_test|\.test|\.spec)\.", name))


class Run:
    def __init__(self, task: str, base: str):
        self.task, self.base = task, base
        self.root = Path(git("rev-parse", "--show-toplevel"))
        self.folder = self.root / "docs" / "tasks" / task
        own = f"docs/tasks/{task}/"
        lines = git("log", "--reverse", "--format=%h %s", f"{base}..HEAD").splitlines()
        self.commits = [(sha, subject.split(":", 1)[0]) for sha, subject in (c.split(" ", 1) for c in lines)
                        if not subject.startswith("kairyn(")]
        self.changed = [p for p in git("diff", "--name-only", f"{base}..HEAD").splitlines() if not p.startswith(own)]

    def files(self, sha: str) -> list:
        return git("show", "--name-only", "--format=", sha).splitlines()

    def edits(self, sha: str, path: str) -> bool:
        """True when the commit changes or removes a line of the file. Adding lines is fine."""
        return any(line.startswith("-") and not line.startswith("---")
                   for line in git("show", "-U0", "--format=", sha, "--", path).splitlines())

    def design(self) -> str:
        path = self.folder / "DESIGN.md"
        return path.read_text() if path.is_file() else ""


def check_design(run: Run, args) -> list:
    text = run.design()
    named = set(re.findall(r"`([^`\s]+)`", text))

    def covered(path: str) -> bool:
        return any(path == n or (n.endswith("/") and path.startswith(n)) or ("*" in n and fnmatch.fnmatch(path, n))
                   for n in named) or any(fnmatch.fnmatch(path, a) for a in args.allow)

    problems = [f"`{p}` changed, but DESIGN.md does not name it" for p in run.changed if not covered(p)]
    for path in (p for p in run.changed if p.endswith("hooks.json")):
        def events(rev: str) -> set:
            raw = git("show", f"{rev}:{path}", check=False)
            try:
                return set(json.loads(raw).get("hooks") or {}) if raw else set()
            except ValueError:
                return set()
        for event in sorted(events("HEAD") - events(run.base)):
            if not re.search(rf"\b{re.escape(event)}\b", text):
                problems.append(f"hook event `{event}` added to `{path}`, but DESIGN.md does not name it")
    return problems


def red(sha: str, command: str) -> int:
    """Exit code of the command in a detached checkout of the commit."""
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "red"
        git("worktree", "add", "-q", "--detach", str(wt), sha)
        try:
            return subprocess.run(command, shell=True, cwd=wt, capture_output=True).returncode
        finally:
            git("worktree", "remove", "--force", str(wt), check=False)


def check_commits(run: Run, args) -> list:
    problems = []
    for sha, label in run.commits:
        tests = [f for f in run.files(sha) if is_test(f)]
        if label.startswith("feat"):
            problems += [f"{sha} {label} changes the test file `{f}`: a green commit changes no test" for f in tests]
            continue
        if GREEN_PAIR.fullmatch(label):
            continue
        edited = [f for f in tests if run.edits(sha, f)]
        if edited and not label.startswith("test"):
            problems += [f"{sha} {label} edits the test file `{f}` in the fix round: edit it in a test commit "
                         "that is red" for f in edited]
        elif edited and red(sha, args.run) == 0:
            problems.append(f"{sha} {label} edits {', '.join(f'`{f}`' for f in edited)} but is not red: "
                            f"`{args.run}` passes there")
    return problems


def check_evals(run: Run, args) -> list:
    plugin = [p for p in run.changed if p.startswith("plugin/")]
    if not plugin:
        return []
    record_path = Path("evals/results/passed.json")
    main = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")).parent
    record = load_record(run.root / record_path) or load_record(main / record_path)
    problems = []
    for config in sorted((run.root / "evals" / "promptfoo").glob("*.yaml")):
        deps = parse_depends(config.read_text())
        hit = next((p for p in plugin if any(fnmatch.fnmatch(p, d) for d in deps)), None)
        if hit and record.get(config.stem) != deps_hash(run.root, deps):
            problems.append(f"eval `{config.stem}` depends on the changed `{hit}` and has no pass at the current "
                            f"hash: run /run-evals {config.stem}")
    return problems


def check_sessions(run: Run, args) -> list:
    manual = [m.group(1) for m in re.finditer(r"^\|\s*(AC\d+)\b[^|]*\|[^|]*\|\s*Manual\b", run.design(), re.M | re.I)]
    runs = "\n".join(p.read_text() for p in sorted(run.folder.glob("*.md")) if p.name != "DESIGN.md")
    return [f"{ac} needs a real session, but no task file has a `Run {ac}: <who>, <time>, \"<what it showed>\"` line"
            for ac in manual if not re.search(rf"^Run {ac}: \S", runs, re.M)]


CHECKS = {"design": check_design, "commits": check_commits, "evals": check_evals, "sessions": check_sessions}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("check", choices=sorted(CHECKS))
    parser.add_argument("--task", help="default: from the branch kairyn/<task>")
    parser.add_argument("--base", help="default: the merge base of HEAD and main")
    parser.add_argument("--allow", action="append", default=[], help="design: a glob for a file DESIGN.md need not name")
    parser.add_argument("--run", default="uv run pytest -q", help="commits: the command that must fail at a red commit")
    args = parser.parse_args(argv)
    task = args.task or git("branch", "--show-current").partition("kairyn/")[2]
    if not task:
        print(f"PASS: {args.check}: not on a kairyn/<task> branch, nothing to check")
        return 0
    base = args.base or git("merge-base", "HEAD", "main", check=False) or git("merge-base", "HEAD", "origin/main")
    run = Run(task, base)
    if not run.commits:
        print(f"PASS: {args.check}: no code commits after {base[:12]}")
        return 0
    problems = CHECKS[args.check](run, args)
    for problem in problems:
        print(f"FAIL: {args.check}: {problem}")
    if not problems:
        print(f"PASS: {args.check}: {len(run.commits)} commits")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
