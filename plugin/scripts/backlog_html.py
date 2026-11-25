#!/usr/bin/env python3
"""Write .kairyn/backlog.html: a view-only page of every idea file in docs/backlog/.

One self-contained file: CSS, JS and data inline, nothing loaded from the network.
Build it on demand; it is git-ignored. /kairyn:backlog runs this script.

Usage (from the repo root):
    python3 backlog_html.py [--root DIR]    # prints the page's path
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BACKLOG = "docs/backlog"
PAGE_PATH = ".kairyn/backlog.html"
IDEA_FILE = re.compile(r"^\d{14}-[\w-]+\.md$")


def split_front_matter(text: str) -> tuple[dict, str]:
    """Return ({key: value}, body). A file without front matter has no fields."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields, m.group(2)


def parse_idea(path: Path) -> dict:
    fields, _body = split_front_matter(path.read_text(encoding="utf-8"))
    return {"file": path.name, "slug": re.sub(r"^\d{14}-|\.md$", "", path.name),
            "title": fields.get("title") or path.stem}


def load_ideas(root: Path) -> list[dict]:
    """Every idea file, newest capture first (the file name starts with its capture time)."""
    files = sorted((p for p in (root / BACKLOG).glob("*.md") if IDEA_FILE.match(p.name)), reverse=True)
    return [parse_idea(p) for p in files]


def _script_json(value) -> str:
    """JSON safe inside a <script> element."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def render_html(root: Path) -> str:
    return PAGE.replace("%DATA%", _script_json(load_ideas(root)))


def build(root: Path) -> Path:
    page = root / PAGE_PATH
    page.write_text(render_html(root), encoding="utf-8")
    return page


def main(argv: list[str]) -> int:
    root = Path(".")
    if argv[:1] == ["--root"] and len(argv) == 2:
        root = Path(argv[1])
    elif argv:
        print("usage: backlog_html.py [--root DIR]", file=sys.stderr)
        return 2
    print(build(root))
    return 0


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Backlog</title>
<style>
body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
</style>
</head>
<body>
<main><h1>Backlog</h1><div id="list"></div></main>
<script>
const DATA=%DATA%;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
document.getElementById("list").innerHTML=DATA.map(d=>`<div>${esc(d.title)}</div>`).join("");
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
