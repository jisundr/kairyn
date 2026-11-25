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
        i["text"] = plain(i["body"] + " " + i["log"]).lower()
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
        if re.match(r"^(https?://|#)", target):
            href = target
        elif re.match(r"^[\w.][\w./#-]*$", target):
            href = "../" + BACKLOG + "/" + target  # idea files link from docs/backlog/; the page is in .kairyn/
        else:
            href = "#"
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


def triage_notes(root: Path) -> str:
    """The "## Next" and "## Parked" sections of TRIAGE.md as HTML, or "" with no TRIAGE.md."""
    triage = root / BACKLOG / "TRIAGE.md"
    if not triage.exists():
        return ""
    sections = re.split(r"^(?=## )", triage.read_text(encoding="utf-8"), flags=re.M)
    keep = [s.strip() for s in sections if re.match(r"## (Next|Parked)[ \t]*(\n|$)", s)]
    return render_markdown("\n\n".join(keep)) if keep else ""


def render_html(root: Path) -> str:
    ideas = load_ideas(root)
    appetites = sorted({i["appetite"] for i in ideas if i["appetite"]})
    options = "".join(f'<option value="{escape(a)}">{escape(a[:1].upper() + a[1:])}</option>' for a in appetites)
    notes = triage_notes(root)
    if notes:
        notes = f'<details class="notes"><summary>Triage notes: Next and Parked, from TRIAGE.md</summary><div class="md">{notes}</div></details>'
    return (PAGE.replace("%APPETITES%", options).replace("%NOTES%", notes)
            .replace("%COUNT%", str(len(ideas))).replace("%DATA%", _script_json(ideas)))


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
:root{--bg:#f5f6f4;--surface:#fff;--fg:#1d2321;--muted:#5f6b66;--line:#dfe3e0;--accent:#2f6f62;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme: dark){:root{--bg:#141917;--surface:#1c2220;--fg:#e4e8e6;--muted:#97a29d;--line:#2c3431;--accent:#6fc2ad;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 var(--sans)}
.wrap{max-width:1000px;margin:0 auto;padding:28px 16px 60px;display:grid;gap:18px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 20px}
h1{font-size:1.8rem;margin:0;letter-spacing:-.01em}
.src{font:12px var(--mono);color:var(--muted)}
.tools{display:flex;flex-wrap:wrap;gap:10px}
.tools input,.tools select{font:inherit;font-size:14px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg)}
.tools input{flex:1 1 240px;min-width:0}
details.notes{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 16px}
details.notes summary{cursor:pointer;font-weight:600;font-size:14px}
#list{display:grid;gap:6px}
.row{display:grid;grid-template-columns:1fr auto;gap:4px 14px;align-items:start;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;cursor:pointer;text-align:left;font:inherit;color:inherit;width:100%}
.row:hover{border-color:var(--muted)}
.row .t{font-weight:600;min-width:0}
.row .m{font:12px var(--mono);color:var(--muted);white-space:nowrap}
.row .s{grid-column:1/3;color:var(--muted);font-size:13.5px;min-width:0}
.app{font:11.5px var(--mono);color:var(--muted);border:1px solid var(--line);padding:1px 7px;border-radius:999px}
.empty{color:var(--muted);padding:24px;text-align:center}
button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.scrim{position:fixed;inset:0;background:rgb(0 0 0 / .35);z-index:20}
.pane{position:fixed;top:0;right:0;bottom:0;width:min(640px,100%);background:var(--surface);border-left:1px solid var(--line);z-index:21;overflow-y:auto;padding:20px 24px 40px}
[hidden]{display:none!important}
.pane .close{position:sticky;top:0;float:right;font:inherit;font-size:13px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:8px;padding:6px 12px;cursor:pointer}
.pane h2{font-size:1.4rem;margin:4px 0 10px;max-width:90%}
.meta{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13px;margin:0 0 16px}
.meta dt{color:var(--muted)}.meta dd{margin:0;font:12.5px var(--mono);overflow-wrap:anywhere}
.md{font-size:14.5px;max-width:65ch;overflow-wrap:anywhere}
.md p{margin:.5em 0}.md ul,.md ol{padding-left:1.2em;margin:.4em 0}
.md h4,.md h5,.md h6{font-size:1rem;margin:1em 0 .3em}
.md blockquote{margin:.5em 0;padding-left:12px;border-left:3px solid var(--line);color:var(--muted)}
.md table{border-collapse:collapse;display:block;overflow-x:auto}.md th,.md td{border:1px solid var(--line);padding:4px 8px;text-align:left}
.md code{font-family:var(--mono);font-size:.88em;background:var(--bg);padding:1px 4px;border-radius:4px}
.md a{color:var(--accent)}
.log{margin-top:20px;border-top:1px solid var(--line);padding-top:12px}
.log h3{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 8px}
.log .md{font-size:13px}
@media (max-width:560px){.row .m{grid-column:1/3}.pane{padding-left:16px;padding-right:16px}}
</style>
</head>
<body>
<div class="wrap">
  <header><h1>Backlog</h1><span class="src">docs/backlog/ · %COUNT% ideas · view only</span></header>
  <div class="tools">
    <input id="q" type="search" placeholder="Search titles and text" aria-label="Search">
    <select id="app" aria-label="Appetite"><option value="">Any appetite</option>%APPETITES%<option value="none">Not set</option></select>
  </div>
  %NOTES%
  <div id="list"></div>
</div>
<div class="scrim" id="scrim" hidden></div>
<aside class="pane" id="pane" hidden role="dialog" aria-modal="true"></aside>
<script>
const DATA=%DATA%;
const bySlug=Object.fromEntries(DATA.map(d=>[d.slug,d]));
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const $=id=>document.getElementById(id);
function renderList(){
  const q=$("q").value.trim().toLowerCase(),ap=$("app").value;
  const items=DATA.filter(d=>(!ap||(ap==="none"?!d.appetite:d.appetite===ap))&&(!q||(d.title+" "+d.slug).toLowerCase().includes(q)||d.text.includes(q)));
  $("list").innerHTML=items.length?items.map(d=>`<button class="row" data-slug="${esc(d.slug)}"><span class="t">${esc(d.title)}</span><span class="m">${d.appetite?`<span class="app">${esc(d.appetite)}</span> `:""}${esc(d.date)}</span><span class="s">${esc(d.problem)||"&nbsp;"}</span></button>`).join("")
    :`<div class="empty">No ideas match. Clear the search or pick another appetite.</div>`;
  $("list").querySelectorAll(".row").forEach(r=>r.onclick=()=>{location.hash=r.dataset.slug});
}
let opener=null;
function openPane(slug){
  const d=bySlug[slug],pane=$("pane");
  if(!d){pane.hidden=true;$("scrim").hidden=true;if(opener){opener.focus();opener=null}return}
  if(pane.hidden)opener=document.activeElement;
  pane.innerHTML=`<button class="close" id="close" type="button">Close</button><h2>${esc(d.title)}</h2>
    <dl class="meta"><dt>Appetite</dt><dd>${esc(d.appetite||"not set")}</dd><dt>Captured</dt><dd>${esc(d.date||"—")}</dd><dt>Review by</dt><dd>${esc(d.review_by||"—")}</dd><dt>Requester</dt><dd>${esc(d.requester||"—")}</dd><dt>File</dt><dd>docs/backlog/${esc(d.file)}</dd></dl>
    <div class="md">${d.body_html}</div>${d.log_html?`<div class="log"><h3>Log</h3><div class="md">${d.log_html}</div></div>`:""}`;
  pane.hidden=false;$("scrim").hidden=false;pane.scrollTop=0;
  $("close").onclick=closePane;$("close").focus();
}
function closePane(){history.replaceState(null,"",location.pathname+location.search);openPane(null)}
$("scrim").onclick=closePane;
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!$("pane").hidden)closePane()});
window.addEventListener("hashchange",()=>openPane(decodeURIComponent(location.hash.slice(1))));
$("q").oninput=renderList;$("app").onchange=renderList;
renderList();
if(location.hash)openPane(decodeURIComponent(location.hash.slice(1)));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
