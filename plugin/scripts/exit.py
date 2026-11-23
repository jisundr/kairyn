#!/usr/bin/env python3
"""The scripted half of the kairyn exit stage: what must always work, so the model does not do it.

    python3 exit.py check <task>                  # OK, or FAIL: <why> (exit 1)
    python3 exit.py adr-path <slug>               # next free docs/adr/<NNNN>-<slug>.md
    python3 exit.py close <task> --entry "<text>" # changelog entry, then delete the task and its backlog files
    python3 exit.py release <version>             # ## Unreleased -> ## <version>, local tag v<version>

All take --root (default: the current directory). A task is done when its STATE.md has
`status: done` and its REQUIREMENTS.md has an approval line. close deletes:
  - docs/tasks/<task>/
  - docs/backlog files with `status: committed` that link the task
  - docs/backlog files with `status: dropped` that link no task folder that still exists
and removes their rows from docs/backlog/README.md. Git history keeps every deleted file.
Its last line is `RETRO: learnings.md <used>/<budget>` when learnings.md is past half its
budget (retro.py): the exit stage then runs the retro stage.
release never pushes: it prints the push command for the user.

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from retro import learnings_size

CHANGELOG = "CHANGELOG.md"
UNRELEASED = "## Unreleased"
STATUS_RE = re.compile(r"^status:\s*([\w-]+)", re.M)
APPROVED_RE = re.compile(r'^Approval: (?!pending\s*$).+, \d{4}-\d\d-\d\dT[\d:]+Z, ".+"\s*$', re.M)
TASK_LINK_RE = re.compile(r"tasks/(\d{4}-\d\d-\d\d-[\w-]+)/")


def fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 1


def status_of(path: Path) -> str | None:
    m = STATUS_RE.search(path.read_text()) if path.is_file() else None
    return m.group(1) if m else None


def task_problem(root: Path, task: str) -> str | None:
    folder = root / "docs" / "tasks" / task
    if not task or "/" in task or not folder.is_dir():
        return f"no task folder docs/tasks/{task}/"
    status = status_of(folder / "STATE.md")
    if status != "done":
        return f"{task} has status {status}, not done"
    req = folder / "REQUIREMENTS.md"
    if not req.is_file() or not APPROVED_RE.search(req.read_text()):
        return f"{task} has no approval line in REQUIREMENTS.md"
    return None


def cmd_check(root: Path, task: str) -> int:
    problem = task_problem(root, task)
    if problem:
        return fail(problem)
    print("OK")
    return 0


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "decision"


def cmd_adr_path(root: Path, slug: str) -> int:
    numbers = [int(m.group(1)) for p in (root / "docs" / "adr").glob("*.md")
               if (m := re.match(r"(\d{4})-", p.name))]
    print(f"docs/adr/{max(numbers, default=0) + 1:04d}-{slugify(slug)}.md")
    return 0


def add_entry(text: str, line: str) -> str:
    """Append line at the end of the Unreleased section, creating the file or the section."""
    if not text.strip():
        text = "# Changelog\n"
    lines = text.rstrip("\n").split("\n")
    if UNRELEASED not in lines:
        at = 1 if lines[0].startswith("# ") else 0
        lines[at:at] = ["", UNRELEASED, ""] if at else [UNRELEASED, ""]
    start = lines.index(UNRELEASED) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    while end > start and not lines[end - 1].strip():
        end -= 1
    body = lines[start:end]
    insert = ([""] if not body else []) + [line]
    lines[end:end] = insert + ([""] if end < len(lines) else [])
    return "\n".join(lines).rstrip("\n") + "\n"


def closed_backlog(root: Path, task: str) -> list[Path]:
    out = []
    for path in sorted((root / "docs" / "backlog").glob("*.md")):
        if path.name == "README.md":
            continue
        text, status = path.read_text(), status_of(path)
        linked = set(TASK_LINK_RE.findall(text))
        live = {t for t in linked if t != task and (root / "docs" / "tasks" / t).is_dir()}
        if (status == "committed" and task in linked) or (status == "dropped" and not live):
            out.append(path)
    return out


def links_to(root: Path, targets: list[str]) -> list[tuple[str, str]]:
    """(file, target) for each markdown file that still names a deleted path."""
    hits = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith((".git/", "node_modules/")) or rel == CHANGELOG or not path.is_file():
            continue
        text = path.read_text(errors="ignore")
        hits += [(rel, t) for t in targets if t in text]
    return hits


def cmd_close(root: Path, task: str, entry: str) -> int:
    problem = task_problem(root, task)
    if problem:
        return fail(problem)
    if not entry.strip():
        return fail("empty --entry")
    log = root / CHANGELOG
    log.write_text(add_entry(log.read_text() if log.is_file() else "", f"- {entry.strip()} ({task})"))
    print(f"WROTE {CHANGELOG}")
    gone = closed_backlog(root, task)
    index = root / "docs" / "backlog" / "README.md"
    if gone and index.is_file():
        old = index.read_text()
        names = [f"]({p.name})" for p in gone]
        new = "".join(l for l in old.splitlines(keepends=True) if not any(n in l for n in names))
        if new != old:
            index.write_text(new)
            print("EDITED docs/backlog/README.md")
    for path in gone:
        path.unlink()
        print(f"DELETED {path.relative_to(root).as_posix()}")
    shutil.rmtree(root / "docs" / "tasks" / task)
    print(f"DELETED docs/tasks/{task}/")
    for rel, target in links_to(root, [f"tasks/{task}/"] + [p.name for p in gone]):
        print(f"LINK: {rel} still links {target}")
    used, budget = learnings_size(root)
    if budget and used * 2 > budget:
        print(f"RETRO: learnings.md {used}/{budget}")
    return 0


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def cmd_release(root: Path, version: str) -> int:
    log = root / CHANGELOG
    lines = log.read_text().rstrip("\n").split("\n") if log.is_file() else []
    if UNRELEASED not in lines:
        return fail(f"no {UNRELEASED} section in {CHANGELOG}")
    start = lines.index(UNRELEASED) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    notes = "\n".join(l for l in lines[start:end]).strip()
    if not notes:
        return fail(f"{UNRELEASED} is empty")
    tag = f"v{version}"
    if git(root, "rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode == 0:
        return fail(f"tag {tag} exists")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines[start - 1:start - 1] = [UNRELEASED, ""]
    lines[start + 1] = f"## {version} - {today}"
    log.write_text("\n".join(lines) + "\n")
    print(f"WROTE {CHANGELOG}")
    made = git(root, "tag", "-a", tag, "-m", f"{tag}\n\n{notes}")
    if made.returncode != 0:
        return fail(f"git tag: {made.stderr.strip()}")
    print(f"TAGGED {tag} (local). Commit {CHANGELOG}, then push with: git push origin {tag}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path("."))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", parents=[common]).add_argument("task")
    sub.add_parser("adr-path", parents=[common]).add_argument("slug")
    close = sub.add_parser("close", parents=[common])
    close.add_argument("task")
    close.add_argument("--entry", required=True)
    sub.add_parser("release", parents=[common]).add_argument("version")
    a = ap.parse_args(argv)
    root = a.root.resolve()
    if a.cmd == "check":
        return cmd_check(root, a.task)
    if a.cmd == "adr-path":
        return cmd_adr_path(root, a.slug)
    if a.cmd == "close":
        return cmd_close(root, a.task, a.entry)
    return cmd_release(root, a.version)


if __name__ == "__main__":
    sys.exit(main())
