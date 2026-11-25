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
from html import escape
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


LOG_HEADING = re.compile(r"^# Log\s*$", re.M)
TIMESTAMP_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT[\d:]+Z)", re.M)
FIELDS = ["title", "appetite", "date", "review_by", "requester"]


def plain(text: str) -> str:
    """Markdown inline text as plain text: no bold, backticks or link targets."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\*\*|`", "", text).strip()


def parse_idea(path: Path) -> dict:
    """One idea file: its front matter fields, slug, problem line, text and log."""
    fields, body = split_front_matter(path.read_text(encoding="utf-8"))
    body = re.sub(r"^\s*# .*\n+", "", body.lstrip("\n"), count=1)  # the title repeats the front matter
    parts = LOG_HEADING.split(body, maxsplit=1)
    problem = re.search(r"\*\*Problem[^*]*\*\*[ \t]*(.*)", parts[0])
    idea = {key: fields.get(key, "") for key in FIELDS}
    idea.update(file=path.name, slug=re.sub(r"^\d{14}-|\.md$", "", path.name),
                title=fields.get("title") or path.stem,
                problem=plain(problem.group(1)) if problem else "",
                body=parts[0].strip(), log=parts[1].strip() if len(parts) > 1 else "")
    return idea


def load_ideas(root: Path) -> list[dict]:
    """Every idea file, newest capture first (the file name starts with its capture time)."""
    files = sorted((p for p in (root / BACKLOG).glob("*.md") if IDEA_FILE.match(p.name)), reverse=True)
    ideas = [parse_idea(p) for p in files]
    links = {i["file"]: "#" + i["slug"] for i in ideas}
    for i in ideas:
        i["body_html"] = render_markdown(i.pop("body"), links)
        i["log_html"] = render_markdown(TIMESTAMP_LINE.sub(r"- \1", i.pop("log")), links)
    return ideas


# ---------- markdown: the subset idea files use ----------

def _inline(text: str, links: dict) -> str:
    out = []
    for i, part in enumerate(re.split(r"(`[^`]*`)", text)):
        if i % 2:
            out.append(f"<code>{escape(part[1:-1])}</code>")
            continue
        part = escape(part, quote=False)
        part = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: _link(m.group(1), m.group(2), links), part)
        part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", part)
        part = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", part)
        out.append(part)
    return "".join(out)


def _link(label: str, target: str, links: dict) -> str:
    """An idea file opens on the page; other targets keep only http(s), relative and # forms (A1)."""
    href = links.get(target)
    if href is None:
        href = target if re.match(r"^(https?://|#|[\w.][\w./#-]*$)", target) else "#"
    return f'<a href="{escape(href)}">{label}</a>'


def render_markdown(text: str, links: dict = None) -> str:
    """Headings, paragraphs, flat lists, blockquotes, tables and inline code, bold, italics and links.

    HTML in the text is escaped. links maps an idea file name to the href to use instead (#slug).
    """
    links = links or {}
    html, para, items, kind = [], [], [], ""

    def flush():
        nonlocal para, items, kind
        if para:
            html.append(f"<p>{_inline(' '.join(para), links)}</p>")
        if items:
            html.append(f"<{kind}>" + "".join(f"<li>{_inline(i, links)}</li>" for i in items) + f"</{kind}>")
        para, items, kind = [], [], ""

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        item = re.match(r"^\s*(?:([-*])|\d+\.) (.*)$", line)
        heading = re.match(r"^(#{1,6}) (.*)$", line)
        if not stripped:
            flush()
        elif heading:
            flush()
            level = min(len(heading.group(1)) + 2, 6)  # the page owns h1 to h3
            html.append(f"<h{level}>{_inline(heading.group(2), links)}</h{level}>")
        elif stripped.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            html.append(f"<blockquote>{render_markdown(chr(10).join(quote), links)}</blockquote>")
            continue
        elif stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s|:-]+\|\s*$", lines[i + 1]):
            flush()
            rows = [lines[i]]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head = "".join(f"<th>{_inline(c, links)}</th>" for c in cells[0])
            body = "".join("<tr>" + "".join(f"<td>{_inline(c, links)}</td>" for c in r) + "</tr>" for r in cells[1:])
            html.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue
        elif item:
            new_kind = "ul" if item.group(1) else "ol"
            if para or (items and kind != new_kind):
                flush()
            kind = new_kind
            items.append(item.group(2))
        elif items and line.startswith(" "):
            items[-1] += " " + stripped  # a wrapped list item
        else:
            if items:
                flush()
            para.append(stripped)
        i += 1
    flush()
    return "\n".join(html)


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
