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
FIELDS = ["title", "effort", "impact", "date", "review_by", "requester"]
LEVELS = ("low", "medium", "high")


def plain(text: str) -> str:
    """Markdown inline text as plain text: no bold, backticks or link targets."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\*\*|`", "", text).strip()


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LOG_ENTRY = re.compile(r"^(?:[-*] )?(\d{4})-(\d\d)-(\d\d)T(\d\d:\d\d)(?::\d\d)?Z\s*(?:\[([^\]]+)\]\s*)?(.*)$")


def first_sentence(text: str) -> str:
    """Up to the first '.', '!' or '?' that ends a word, or all of the text."""
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text


def level(value: str) -> str:
    """'low', 'medium' or 'high' from the value's first word, in any case; else '' (not set)."""
    m = re.match(r"\s*([A-Za-z]+)\b", value)
    word = m.group(1).lower() if m else ""
    return word if word in LEVELS else ""


def date_label(value: str) -> str:
    m = re.match(r"^\d{4}-(\d\d)-(\d\d)$", value)
    if not m or not 1 <= int(m.group(1)) <= 12:
        return value or "—"
    return f"{MONTHS[int(m.group(1)) - 1]} {int(m.group(2))}"


def split_problem(body: str) -> tuple[str, str]:
    """(the **Problem...** paragraph, the body without it). No problem: ("", body)."""
    blocks = re.split(r"\n\s*\n", body)
    for n, block in enumerate(blocks):
        if block.lstrip().startswith("**Problem"):
            return block.strip(), "\n\n".join(blocks[:n] + blocks[n + 1:])
    return "", body


def parse_idea(path: Path) -> dict:
    """One idea file: its front matter fields, slug, problem line, text and log."""
    fields, body = split_front_matter(path.read_text(encoding="utf-8"))
    body = re.sub(r"^\s*# .*\n+", "", body.lstrip("\n"), count=1)  # the title repeats the front matter
    parts = LOG_HEADING.split(body, maxsplit=1)
    problem, rest = split_problem(parts[0].strip())
    idea = {key: fields.get(key, "") for key in FIELDS}
    text = re.sub(r"^\*\*Problem[^*]*\*\*[ \t]*", "", problem.split("\n")[0])  # the problem line
    idea.update(file=path.name, slug=re.sub(r"^\d{14}-|\.md$", "", path.name),
                title=fields.get("title") or path.stem,
                problem=first_sentence(plain(text)) if problem else "",
                effort_level=level(fields.get("effort", "")),
                impact_level=level(fields.get("impact", "")),
                date_label=date_label(fields.get("date", "")),
                lead=problem, body=rest, log=parts[1].strip() if len(parts) > 1 else "")
    return idea


def render_log(text: str, links: dict) -> str:
    """The # Log section as a timeline: one <li> per entry with its time, tag and text.

    An entry starts with a UTC timestamp, with or without a list dash; an indented line continues it.
    """
    entries = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = LOG_ENTRY.match(line.strip())
        if m:
            year, month, day, hhmm, tag, rest = m.groups()
            stamp = re.match(r"^(?:[-*] )?(\S+)", line.strip()).group(1)
            entries.append([f'<time datetime="{escape(stamp)}">{MONTHS[int(month) - 1]} {int(day)} {hhmm}</time>', tag, rest])
        elif entries and line[:1].isspace():
            entries[-1][2] += " " + line.strip()
        else:
            entries.append(["<time></time>", None, re.sub(r"^[-*] ", "", line.strip())])
    items = ""
    for when, tag, rest in entries:
        chip = '<span class="tag">' + escape(tag) + "</span> " if tag else ""
        items += f"<li>{when}<div>{chip}{_inline(rest, links)}</div></li>"
    return f'<ol class="tl">{items}</ol>' if items else ""


def load_ideas(root: Path) -> list[dict]:
    """Every idea file, newest capture first (the file name starts with its capture time)."""
    files = sorted((p for p in (root / BACKLOG).glob("*.md") if IDEA_FILE.match(p.name)), reverse=True)
    ideas = [parse_idea(p) for p in files]
    links = {i["file"]: "#" + i["slug"] for i in ideas}
    for i in ideas:
        i["text"] = plain(i["lead"] + " " + i["body"] + " " + i["log"]).lower()
        i["problem_html"] = _inline(" ".join(i.pop("lead").split()), links)
        i["body_html"] = render_markdown(i.pop("body"), links)
        i["log_html"] = render_log(i.pop("log"), links)
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
    options = ""  # T2 replaces the appetite filter
    notes = triage_notes(root)
    if notes:
        notes = f'<details class="notes"><summary>Triage notes: Next and Parked, from TRIAGE.md</summary><div class="md">{notes}</div></details>'
    return (PAGE.replace("%APPETITES%", options).replace("%NOTES%", notes)
            .replace("%COUNT%", str(len(ideas))).replace("%DATA%", _script_json(ideas)))


class NothingToBuild(Exception):
    """The repo has no .kairyn/ or no idea files. The message is one line for the user."""


def ignore_page(root: Path) -> None:
    """Add PAGE_PATH to the repo's .gitignore once, creating the file if it is missing."""
    gitignore = root / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if PAGE_PATH in (line.strip() for line in text.splitlines()):
        return
    if text and not text.endswith("\n"):
        text += "\n"
    gitignore.write_text(text + PAGE_PATH + "\n", encoding="utf-8")


def build(root: Path) -> Path:
    """Write the page and git-ignore it. Raise NothingToBuild if there is nothing to build."""
    if not (root / ".kairyn").is_dir():
        raise NothingToBuild("FAIL: no .kairyn/ here. Run /kairyn:init first.")
    if not any(IDEA_FILE.match(p.name) for p in (root / BACKLOG).glob("*.md")):
        raise NothingToBuild(f"FAIL: no idea files in {BACKLOG}/ (named <YYYYMMDDHHMMSS>-<slug>.md).")
    page = root / PAGE_PATH
    page.write_text(render_html(root), encoding="utf-8")
    ignore_page(root)
    return page


def main(argv: list[str]) -> int:
    root = Path(".")
    if argv[:1] == ["--root"] and len(argv) == 2:
        root = Path(argv[1])
    elif argv:
        print("usage: backlog_html.py [--root DIR]", file=sys.stderr)
        return 2
    try:
        page = build(root)
    except NothingToBuild as e:
        print(e)
        return 1
    print(page)
    return 0


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Backlog</title>
<style>
:root{--bg:#f6f7f6;--surface:#fff;--fg:#1b1f1e;--muted:#5c6763;--faint:#717c77;--line:#e3e6e4;--hover:#f2f4f3;--accent:#2f6f62;--mark:#fdf0b3;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme: dark){:root{--bg:#121615;--surface:#191e1c;--fg:#e6eae8;--muted:#9da8a3;--faint:#8a958f;--line:#29302d;--hover:#202624;--accent:#6fc2ad;--mark:#5a4b12;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:880px;margin:0 auto;padding:32px 16px 64px;display:grid;grid-template-columns:minmax(0,1fr);gap:16px}
header h1{font-size:1.6rem;line-height:1.2;margin:0 0 4px;letter-spacing:-.01em}
header p{margin:0;color:var(--muted);font-size:14px}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.tools input,.tools select{font:inherit;font-size:14px;padding:7px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg);min-width:0;max-width:100%}
.tools input{flex:1 1 260px}
.count{color:var(--muted);font-size:13px;margin-left:auto;font-variant-numeric:tabular-nums}
details.notes{border:1px solid var(--line);border-radius:10px;background:var(--surface);padding:10px 16px;font-size:14px}
details.notes summary{cursor:pointer;color:var(--muted);font-weight:500}
.list{background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 16px;align-items:baseline;width:100%;padding:10px 16px;border:0;border-bottom:1px solid var(--line);background:none;font:inherit;color:inherit;text-align:left;cursor:pointer}
.row:last-child{border-bottom:0}
.row:hover{background:var(--hover)}
.row .t{font-weight:600;font-size:15px;min-width:0;overflow-wrap:anywhere}
.row .s{grid-column:1;color:var(--muted);font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.row .s.none{color:var(--faint);font-style:italic}
.row .m{grid-row:1/3;grid-column:2;display:flex;gap:10px;align-items:center;font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.lv{display:inline-block;min-width:104px;text-align:center;border:1px solid var(--line);border-radius:999px;padding:1px 8px;font-size:12px}
.lv b{font-weight:500;color:var(--faint)}
.lv.unset{border-style:dashed;color:var(--faint)}
.date{width:48px;text-align:right}
mark{background:var(--mark);color:inherit;border-radius:2px}
.empty{color:var(--muted);padding:24px;text-align:center}
button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.scrim{position:fixed;inset:0;background:rgb(0 0 0 / .35);z-index:20}
.pane{position:fixed;top:0;right:0;bottom:0;width:min(680px,100%);background:var(--surface);border-left:1px solid var(--line);z-index:21;overflow-y:auto;overflow-x:hidden;padding:20px 28px 48px}
[hidden]{display:none!important}
.pane .close{position:sticky;top:0;float:right;font:inherit;font-size:13px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:8px;padding:5px 12px;cursor:pointer}
.pane h2{font-size:1.35rem;line-height:1.3;margin:4px 80px 10px 0;overflow-wrap:anywhere}
.facts{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--muted);margin:0 0 6px}
.facts b{font-weight:500;color:var(--fg)}
.file{font:12px var(--mono);color:var(--faint);margin:0 0 18px;overflow-wrap:anywhere}
.lead{border-left:3px solid var(--accent);padding:2px 0 2px 14px;margin:0 0 16px;font-size:15.5px;line-height:1.55}
.md{font-size:15px;line-height:1.6;max-width:68ch;overflow-wrap:anywhere}
.md p{margin:.6em 0}.md ul,.md ol{padding-left:1.2em;margin:.4em 0}.md li{margin:.2em 0}
.md h4,.md h5,.md h6{font-size:1rem;margin:1em 0 .3em}
.md blockquote{margin:.5em 0;padding-left:12px;border-left:3px solid var(--line);color:var(--muted)}
.md table{border-collapse:collapse;display:block;overflow-x:auto}.md th,.md td{border:1px solid var(--line);padding:4px 8px;text-align:left}
.md code,.tl code{font-family:var(--mono);font-size:.86em;background:var(--hover);padding:1px 4px;border-radius:4px}
.md a,.tl a{color:var(--accent)}
.log{margin-top:28px;border-top:1px solid var(--line);padding-top:14px}
.log h3{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 10px}
.tl{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.tl li{display:grid;grid-template-columns:92px minmax(0,1fr);gap:2px 12px;font-size:14px;line-height:1.5;overflow-wrap:anywhere}
.tl time{font-size:12px;color:var(--faint);font-variant-numeric:tabular-nums;padding-top:2px}
.tag{display:inline-block;font-size:11.5px;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 5px;margin-right:4px}
@media (max-width:560px){.row{grid-template-columns:minmax(0,1fr)}.row .m{grid-row:auto;grid-column:1;order:3}.lv{min-width:0}.date{width:auto}.row .s{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.pane{padding:16px 16px 40px}.tl li{grid-template-columns:minmax(0,1fr)}.count{width:100%;margin:0}}
</style>
</head>
<body>
<div class="wrap">
  <header><h1>Backlog</h1><p>%COUNT% ideas in docs/backlog/, newest first. View only.</p></header>
  <div class="tools">
    <input id="q" type="search" placeholder="Search titles and text  ( / )" aria-label="Search">
    <select id="app" aria-label="Appetite"><option value="">Any appetite</option>%APPETITES%<option value="none">Not set</option></select>
    <span class="count" id="count" aria-live="polite"></span>
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
const LABEL={low:"Low",medium:"Medium",high:"High"};
function chip(d,key,name){
  const v=d[key+"_level"],raw=d[key];
  return `<span class="lv ${key}${v?"":" unset"}" title="${esc(name+": "+(raw||"not set"))}"><b>${name}</b> ${v?LABEL[v]:"Not set"}</span>`;
}
function hi(text,q){
  const t=String(text),i=q?t.toLowerCase().indexOf(q):-1;
  return i<0?esc(t):esc(t.slice(0,i))+"<mark>"+esc(t.slice(i,i+q.length))+"</mark>"+esc(t.slice(i+q.length));
}
function renderList(){
  const q=$("q").value.trim().toLowerCase(),ap=$("app").value;
  const items=DATA.filter(d=>(!ap||(ap==="none"?!d.appetite:d.appetite===ap))&&(!q||(d.title+" "+d.slug).toLowerCase().includes(q)||d.text.includes(q)));
  $("count").textContent=items.length===DATA.length?`${DATA.length} ideas`:`${items.length} of ${DATA.length}`;
  if(!items.length){$("list").innerHTML=`<div class="list"><div class="empty">No ideas match. Clear the search or pick another appetite.</div></div>`;return}
  $("list").innerHTML=`<div class="list">`+items.map(d=>`<button class="row" data-slug="${esc(d.slug)}"><span class="t">${hi(d.title,q)}</span>`+
    `<span class="m">${chip(d,"impact","Impact")}${chip(d,"effort","Effort")}<span class="date" title="${esc(d.date)}">${esc(d.date_label)}</span></span>`+
    `<span class="s${d.problem?"":" none"}">${d.problem?hi(d.problem,q):"No problem statement"}</span></button>`).join("")+`</div>`;
  $("list").querySelectorAll(".row").forEach(r=>r.onclick=()=>{location.hash=r.dataset.slug});
}
let opener=null;
function openPane(slug){
  const d=bySlug[slug],pane=$("pane");
  if(!d){pane.hidden=true;$("scrim").hidden=true;if(opener){opener.focus();opener=null}return}
  if(pane.hidden)opener=document.activeElement;
  const facts=[["Impact",d.impact||"not set"],["Effort",d.effort||"not set"],["Captured",d.date||"—"],["Review by",d.review_by||"—"],["Requester",d.requester||"—"]];
  pane.innerHTML=`<button class="close" id="close" type="button">Close</button><h2>${esc(d.title)}</h2>
    <div class="facts">${facts.map(([k,v])=>`<span>${k} <b>${esc(v)}</b></span>`).join("")}</div>
    <div class="file">docs/backlog/${esc(d.file)}</div>${d.problem_html?`<div class="lead md">${d.problem_html}</div>`:""}
    <div class="md">${d.body_html}</div>${d.log_html?`<div class="log"><h3>Log</h3>${d.log_html}</div>`:""}`;
  pane.hidden=false;$("scrim").hidden=false;pane.scrollTop=0;
  $("close").onclick=closePane;$("close").focus();
}
function closePane(){history.replaceState(null,"",location.pathname+location.search);openPane(null)}
$("scrim").onclick=closePane;
document.addEventListener("keydown",e=>{
  if(e.key==="Escape"&&!$("pane").hidden)closePane();
  else if(e.key==="/"&&$("pane").hidden&&document.activeElement!==$("q")){e.preventDefault();$("q").focus()}
});
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
