#!/usr/bin/env python3
"""The scripted half of the kairyn backlog stage: every idea file write.

    python3 backlog.py capture --slug <slug> --title <t> --effort <level> --impact <level> \\
        --request <the user's words> --problem <draft> [--requester <name>]

    python3 backlog.py digest
    python3 backlog.py decide <idea file> keep|park|renew|drop --reason <why> \\
        [--by <YYYY-MM-DD>] [--effort <level> --impact <level>]
    python3 backlog.py commit <idea file>

All take --root (default: the current directory). capture writes
docs/backlog/<UTC YYYYMMDDHHMMSS>-<slug>.md with status inbox, and creates the folder and its
README.md if missing. It never overwrites a file: it prints one FAIL: line and exits 1.

digest changes nothing. It prints one line per inbox idea and per parked idea whose review_by is
before today (UTC).

decide records the owner's decision (git config user.name): status, review_by (park, renew), a
[triage] log line and the README.md row, which only a kept idea has. keep needs --effort and
--impact; park and renew need --by. A refused decision prints one FAIL: line and changes nothing.

commit starts a task from a triaged idea: docs/tasks/<UTC date>-<slug>/STATE.md from
.kairyn/templates/STATE.md, status committed, a [commit] log line, and no README.md row. It prints
the grill and requirements commands. A refused commit prints one FAIL: line and changes nothing.

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import atomic_write

BACKLOG = "docs/backlog"
LEVELS = ("low", "medium", "high")
DECISIONS = {"keep": ("triaged", "Kept"), "park": ("parked", "Parked"),
             "renew": ("parked", "Park renewed"), "drop": ("dropped", "Dropped")}
TABLE = "| Idea | Effort | Impact | Notes |"
README = """# Backlog

Triaged ideas.

| Idea | Effort | Impact | Notes |
|---|---|---|---|
"""


def slug_arg(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", value):
        raise argparse.ArgumentTypeError(f"{value!r} is not lower-case words joined by hyphens")
    return value


def date_arg(value: str) -> str:
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value).isoformat()
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"{value!r} is not a YYYY-MM-DD date")


def split_idea(text: str) -> tuple[list[str], str] | None:
    """The front matter lines and the rest of an idea file, or None if it has no front matter."""
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    return (match[1].split("\n"), match[2]) if match else None


def field(lines: list[str], key: str) -> str:
    value = next((line[len(key) + 1:].strip() for line in lines if line.startswith(f"{key}:")), "")
    if value.startswith('"'):
        try:
            return json.loads(value)
        except ValueError:
            return value.strip('"')
    return value


def set_field(lines: list[str], key: str, value: str) -> None:
    for i, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[i] = f"{key}: {value}"
            return
    lines.append(f"{key}: {value}")


def index_text(text: str, name: str, title: str, effort: str, impact: str, keep: bool) -> str | None:
    """README.md with the idea's row added, updated or removed. None: a row to add has no table."""
    lines = text.split("\n")
    mine = [i for i, line in enumerate(lines) if line.startswith("| [") and f"]({name})" in line]
    if not keep:
        return "\n".join(line for i, line in enumerate(lines) if i not in mine)
    if mine:  # the owner's link text and notes stay
        cells = re.split(r"(?<!\\)\|", lines[mine[0]])
        cells[2:4] = [f" {effort} ", f" {impact} "]
        lines[mine[0]] = "|".join(cells)
        return "\n".join(lines)
    if TABLE not in lines:
        return None
    end = lines.index(TABLE)
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    cell = title.replace("|", "\\|")
    lines.insert(end, f"| [{cell}]({name}) | {effort} | {impact} | |")
    return "\n".join(lines)


def git_user(root: Path) -> str:
    result = subprocess.run(["git", "-C", str(root), "config", "user.name"], capture_output=True, text=True)
    return result.stdout.strip()


def fail(why: str) -> int:
    print(f"FAIL: {why}; nothing changed")
    return 1


def is_idea(root: Path, path: Path) -> bool:
    return path.parent == root / BACKLOG and path.name != "README.md" and path.is_file()


def add_log(body: str, line: str) -> str:
    if "\n# Log\n" not in body:
        body = body.rstrip("\n") + "\n\n# Log\n\n"
    return body.rstrip("\n") + f"\n{line}\n"


def capture(root: Path, a: argparse.Namespace) -> int:
    requester = a.requester or git_user(root)
    if not requester:
        print("FAIL: no requester: set git config user.name or pass --requester")
        return 1
    now = datetime.now(timezone.utc)
    title = " ".join(a.title.split())
    folder = root / BACKLOG
    path = folder / f"{now:%Y%m%d%H%M%S}-{a.slug}.md"
    # json.dumps gives a quoted string that YAML reads, whatever the text holds.
    text = f"""---
title: {json.dumps(title, ensure_ascii=False)}
status: inbox
requester: {json.dumps(requester, ensure_ascii=False)}
date: {now:%Y-%m-%d}
effort: {a.effort}
impact: {a.impact}
review_by:
---

# {title}

**Raw request:** {a.request}

**Problem (AI draft):** {" ".join(a.problem.split())}

# Log

{now:%Y-%m-%dT%H:%M:%SZ} [capture] Captured for {requester}. Status inbox. Effort {a.effort}, impact {a.impact} proposed by the AI.
"""
    folder.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(text)
    except FileExistsError:
        print(f"FAIL: {path.relative_to(root).as_posix()} exists; nothing changed")
        return 1
    try:
        with (folder / "README.md").open("x", encoding="utf-8") as f:
            f.write(README)
    except FileExistsError:
        pass  # the user's index stays as it is
    print(path.relative_to(root).as_posix())
    return 0


def digest(root: Path) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    found = []
    for path in sorted((root / BACKLOG).glob("*.md")):
        parts = split_idea(path.read_text(encoding="utf-8"))
        if path.name == "README.md" or not parts:
            continue
        meta = parts[0]
        status, by = field(meta, "status"), field(meta, "review_by")
        if status == "parked" and by and by < today:
            status = f"parked, review_by {by}"
        elif status != "inbox":
            continue
        found.append(f"{BACKLOG}/{path.name} | {status} | effort {field(meta, 'effort')} | "
                     f"impact {field(meta, 'impact')} | {field(meta, 'title')}")
    print("\n".join(found) if found else "Nothing to triage.")
    return 0


def decide(root: Path, a: argparse.Namespace) -> int:
    owner = git_user(root)
    path = (root / a.file).resolve()
    reason = " ".join(a.reason.split()).rstrip(".")
    if not owner:
        return fail("no owner: set git config user.name")
    if not is_idea(root, path):
        return fail(f"{a.file} is not an idea file in {BACKLOG}/")
    if not reason:
        return fail("--reason is empty")
    if a.decision in ("park", "renew") and not a.by:
        return fail(f"{a.decision} needs --by, the owner's review date")
    if a.decision == "keep" and not (a.effort and a.impact):
        return fail("keep needs --effort and --impact, as the owner confirms them")
    parts = split_idea(path.read_text(encoding="utf-8"))
    if not parts:
        return fail(f"{a.file} has no front matter")
    meta, body = parts
    status, verb = DECISIONS[a.decision]
    set_field(meta, "status", status)
    note = f"{verb}: {reason}. Status {status}."
    if status == "parked":
        set_field(meta, "review_by", a.by)
        note += f" Review by {a.by}."
    if a.decision == "keep":
        set_field(meta, "effort", a.effort)
        set_field(meta, "impact", a.impact)
        note += f" Effort {a.effort}, impact {a.impact} confirmed by {owner}."
    now = datetime.now(timezone.utc)
    body = add_log(body, f"{now:%Y-%m-%dT%H:%M:%SZ} [triage] {note} Decided by {owner}.")

    readme = root / BACKLOG / "README.md"
    keep = status == "triaged"
    before = readme.read_text(encoding="utf-8") if readme.is_file() else None
    after = index_text(before if before is not None else README, path.name, field(meta, "title") or path.stem,
                       field(meta, "effort"), field(meta, "impact"), keep)
    if after is None:
        return fail(f"{BACKLOG}/README.md has no '{TABLE}' table")
    atomic_write.write_text(path, "\n".join(["---", *meta, "---", body]))
    if after != before and (keep or before is not None):
        atomic_write.write_text(readme, after)
    print(f"{path.relative_to(root).as_posix()}: {status}")
    return 0


def commit(root: Path, file: str) -> int:
    owner = git_user(root)
    path = (root / file).resolve()
    if not owner:
        return fail("no owner: set git config user.name")
    if not is_idea(root, path):
        return fail(f"{file} is not an idea file in {BACKLOG}/")
    parts = split_idea(path.read_text(encoding="utf-8"))
    if not parts:
        return fail(f"{file} has no front matter")
    meta, body = parts
    status = field(meta, "status")
    if status != "triaged":
        return fail(f"{file} has status '{status}'; only a triaged idea can be committed")
    template = root / ".kairyn" / "templates" / "STATE.md"
    summary = "<one-line summary of the request>"
    state = template.read_text(encoding="utf-8") if template.is_file() else ""
    if summary not in state:  # without it STATE.md could not name the idea
        return fail(f".kairyn/templates/STATE.md is missing or has no '{summary}'")

    now = datetime.now(timezone.utc)
    stamp = f"{now:%Y-%m-%dT%H:%M:%SZ}"
    task = f"{now:%Y-%m-%d}-{re.sub(r'^[0-9]{14}-', '', path.stem)}"
    folder = f"docs/tasks/{task}"
    name = path.relative_to(root).as_posix()
    for placeholder, value in (("<YYYY-MM-DD>-<slug>", task), ("<YYYY-MM-DDTHH:MM:SSZ>", stamp),
                               ("<task title>", json.dumps(field(meta, "title") or path.stem, ensure_ascii=False)),
                               (summary, f"Idea: {name}.")):
        state = state.replace(placeholder, value)
    set_field(meta, "status", "committed")
    body = add_log(body, f"{stamp} [commit] Committed by {owner}. Task {folder}/. Status committed.")
    readme = root / BACKLOG / "README.md"
    before = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    after = index_text(before, path.name, "", "", "", keep=False)

    try:
        (root / folder).mkdir(parents=True)
    except FileExistsError:
        return fail(f"{folder}/ exists")
    atomic_write.write_text(root / folder / "STATE.md", state)
    atomic_write.write_text(path, "\n".join(["---", *meta, "---", body]))
    if after != before:
        atomic_write.write_text(readme, after)
    print(f"{name}: committed\n/kairyn:grill {folder}\n/kairyn:requirements {folder}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--root", type=Path, default=Path("."))
    c.add_argument("--slug", type=slug_arg, required=True)
    for name in ("--title", "--request", "--problem"):
        c.add_argument(name, required=True)
    for name in ("--effort", "--impact"):
        c.add_argument(name, choices=LEVELS, required=True)
    c.add_argument("--requester")
    sub.add_parser("digest").add_argument("--root", type=Path, default=Path("."))
    d = sub.add_parser("decide")
    d.add_argument("--root", type=Path, default=Path("."))
    d.add_argument("file")
    d.add_argument("decision", choices=DECISIONS)
    d.add_argument("--reason", required=True)
    d.add_argument("--by", type=date_arg)
    for name in ("--effort", "--impact"):
        d.add_argument(name, choices=LEVELS)
    m = sub.add_parser("commit")
    m.add_argument("--root", type=Path, default=Path("."))
    m.add_argument("file")
    a = ap.parse_args(argv)
    root = a.root.resolve()
    if a.cmd == "digest":
        return digest(root)
    if a.cmd == "commit":
        return commit(root, a.file)
    return capture(root, a) if a.cmd == "capture" else decide(root, a)


if __name__ == "__main__":
    sys.exit(main())
