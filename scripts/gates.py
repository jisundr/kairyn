"""Review gates for this repo's AFK runs. `.kairyn/afk.yml` `gates:` runs each one as a command.
afk.py runs the design, commits and sessions review gates itself; this one is for this repo only.

  evals     after a plugin/ change, each eval that depends on a changed file has a pass at the current hash

Each gate reads the commits on the branch kairyn/<task> after its merge base with main. With no code
commits (readiness runs gates on the base commit) every gate passes. Exit 0 passes; exit 1 lists each problem.
"""
import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from selector import deps_hash, load_record, parse_depends

def git(*args: str, cwd: Path = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode:
        raise SystemExit(f"FAIL: git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


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


CHECKS = {"evals": check_evals}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("check", choices=sorted(CHECKS))
    parser.add_argument("--task", help="default: from the branch kairyn/<task>")
    parser.add_argument("--base", help="default: the merge base of HEAD and main")
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
