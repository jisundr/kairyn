"""This repo's `evals:` command for afk.py's evals review gate (.kairyn/afk.yml, paths `plugin/**`).

    python3 scripts/evals_gate.py

Each eval that depends on a plugin/ file changed after the base has a pass at the current hash in
evals/results/passed.json, in this checkout or the main one. The base: KAIRYN_BASE (afk.py sets it),
else the merge base of HEAD and main. Exit 0 passes; exit 1 lists each eval to run.
"""
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from selector import deps_hash, load_record, parse_depends

RECORD = Path("evals/results/passed.json")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> int:
    root = Path(git("rev-parse", "--show-toplevel") or ".")
    base = os.environ.get("KAIRYN_BASE") or git("merge-base", "HEAD", "main") or git("merge-base", "HEAD", "origin/main")
    if not base:
        print("FAIL: evals: no base commit: set KAIRYN_BASE or add a main branch")
        return 1
    plugin = [p for p in git("diff", "--name-only", f"{base}..HEAD").splitlines() if p.startswith("plugin/")]
    main_root = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")).parent
    record = load_record(root / RECORD) or load_record(main_root / RECORD)
    problems = []
    for config in sorted((root / "evals" / "promptfoo").glob("*.yaml")):
        deps = parse_depends(config.read_text())
        hit = next((p for p in plugin if any(fnmatch.fnmatch(p, d) for d in deps)), None)
        if hit and record.get(config.stem) != deps_hash(root, deps):
            problems.append(f"eval `{config.stem}` depends on the changed `{hit}` and has no pass at the current "
                            f"hash: run /run-evals {config.stem}")
    for problem in problems:
        print(f"FAIL: evals: {problem}")
    if not problems:
        print(f"PASS: evals: {len(plugin)} changed plugin/ files, each eval that depends on one has a pass")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
