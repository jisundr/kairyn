#!/usr/bin/env python3
"""Render docs/backlog/*.md and the Next and Parked notes of TRIAGE.md as one HTML page for people.

Ideas are grouped by status, with filters, search and a detail pane for each idea's text and log.
The page is built from the backlog files, so rebuild it whenever they change. Standard library only;
the markdown is rendered here, so the page needs no script from the network.

Usage (from the repo root):
    python3 scripts/backlog_html.py [--root DIR] [--out PATH]   # default: docs/backlog/backlog.html (git-ignored)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

BACKLOG = Path("docs/backlog")
DEFAULT_OUT = BACKLOG / "backlog.html"
IDEA_FILE = re.compile(r"^\d{14}-[\w-]+\.md$")
STATUSES = ["committed", "shaped", "shaping", "triaged", "inbox", "parked", "dropped"]
FIELDS = ["title", "status", "appetite", "date", "review_by", "requester"]
LOG_HEADING = re.compile(r"^# Log\s*$", re.M)
TIMESTAMP_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT[\d:]+Z)", re.M)


# ---------- parsing ----------

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


def plain(text: str) -> str:
    """Markdown inline text as plain text: no bold, backticks or link targets."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\*\*|`", "", text).strip()


def parse_idea(path: Path) -> dict:
    """One idea file as a dict: its front matter fields, slug, body, log and a one-line summary."""
    fields, body = split_front_matter(path.read_text(encoding="utf-8"))
    body = re.sub(r"^\s*# .*\n+", "", body.lstrip("\n"), count=1)  # the title repeats the front matter
    parts = LOG_HEADING.split(body, maxsplit=1)
    main = parts[0].strip()
    log = parts[1].strip() if len(parts) > 1 else ""
    problem = re.search(r"\*\*Problem[^*]*\*\*\s*(.*)", main)
    idea = {key: fields.get(key, "") for key in FIELDS}
    idea.update(
        file=path.name,
        slug=re.sub(r"^\d{14}-|\.md$", "", path.name),
        title=fields.get("title") or path.stem,
        summary=plain(problem.group(1))[:400] if problem else "",
        body=main,
        log=log,
    )
    return idea


def load_ideas(backlog: Path) -> list[dict]:
    return [parse_idea(p) for p in sorted(backlog.iterdir()) if IDEA_FILE.match(p.name)]


def triage_notes(text: str) -> str:
    """The "## Next" and "## Parked" sections of TRIAGE.md, in file order."""
    sections = re.split(r"^(?=## )", text, flags=re.M)
    keep = [s.strip() for s in sections if re.match(r"## (Next|Parked)\s*$", s.splitlines()[0] if s else "")]
    return "\n\n".join(keep)


# ---------- markdown (the subset backlog files use) ----------

def _inline(text: str, links: dict[str, str]) -> str:
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


def _link(label: str, target: str, links: dict[str, str]) -> str:
    href = links.get(target)
    if href is None:
        href = target if re.match(r"^(https?:|#|[\w./-]+$)", target) else "#"
    return f'<a href="{escape(href)}">{label}</a>'


def render_markdown(text: str, links: dict[str, str] | None = None) -> str:
    """Headings, paragraphs, flat lists, blockquotes, tables and inline code, bold, italics and links.

    links maps a link target (an idea file name) to the href to use instead (#slug).
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
        bullet = re.match(r"^\s*[-*] (.*)$", line)
        number = re.match(r"^\s*\d+\. (.*)$", line)
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
        elif bullet or number:
            new_kind = "ul" if bullet else "ol"
            if para or (items and kind != new_kind):
                flush()
            kind = new_kind
            items.append((bullet or number).group(1))
        elif items and line.startswith(" "):
            items[-1] += " " + stripped  # a wrapped list item
        else:
            if items:
                flush()
            para.append(stripped)
        i += 1
    flush()
    return "\n".join(html)


def render_log(text: str, links: dict[str, str]) -> str:
    """A log section; lines that start with a timestamp are list items even without a dash."""
    return render_markdown(TIMESTAMP_LINE.sub(r"- \1", text), links)


# ---------- page ----------

def page_data(root: Path) -> tuple[list[dict], str]:
    backlog = root / BACKLOG
    ideas = load_ideas(backlog)
    links = {idea["file"]: "#" + idea["slug"] for idea in ideas}
    for idea in ideas:
        idea["body_html"] = render_markdown(idea["body"], links)
        idea["log_html"] = render_log(idea["log"], links) if idea["log"] else ""
    triage = backlog / "TRIAGE.md"
    notes = render_markdown(triage_notes(triage.read_text(encoding="utf-8")), links) if triage.exists() else ""
    return ideas, notes


def _git_head(root: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    except OSError:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def _script_json(value) -> str:
    """JSON safe inside a <script> element."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def render_html(root: Path, generated: datetime | None = None, commit: str | None = None) -> str:
    ideas, notes = page_data(root)
    generated = generated or datetime.now(timezone.utc)
    commit = _git_head(root) if commit is None else commit
    source = "docs/backlog/" + (f" · {commit}" if commit else "") + f" · built {generated:%Y-%m-%d %H:%M} UTC"
    statuses = STATUSES + sorted({i["status"] for i in ideas} - set(STATUSES))
    appetites = sorted({i["appetite"] for i in ideas if i["appetite"]})
    keep = ["file", "slug", "title", "status", "appetite", "date", "review_by", "requester",
            "summary", "body", "body_html", "log_html"]
    data = [{k: i[k] for k in keep} for i in ideas]
    options = "".join(f'<option value="{escape(a)}">{escape(a.capitalize())}</option>' for a in appetites)
    return (PAGE
            .replace("%SOURCE%", escape(source))
            .replace("%APPETITES%", options)
            .replace("%NOTES%", notes or "<p>No TRIAGE.md notes.</p>")
            .replace("%DATA%", _script_json(data))
            .replace("%ORDER%", _script_json(statuses)))


def write_html(root: Path, out: Path, generated: datetime | None = None) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(root, generated), encoding="utf-8")


def main(argv: list[str]) -> int:
    root, out = Path("."), None
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag in ("--root", "--out") and args:
            value = Path(args.pop(0))
            root, out = (value, out) if flag == "--root" else (root, value)
        else:
            print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
            return 2
    if not (root / BACKLOG).is_dir():
        print(f"no {BACKLOG} under {root}", file=sys.stderr)
        return 1
    out = out or root / DEFAULT_OUT
    write_html(root, out)
    print(f"wrote {out}")
    return 0


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Kairyn Backlog</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@500;600&display=swap">
<style>
/* Layout: filter bar over a status-grouped list; a detail pane slides in on the right (full screen on phones). */
:root{
  --bg:#f5f6f4; --surface:#ffffff; --fg:#1d2321; --muted:#5f6b66; --line:#dfe3e0; --accent:#2f6f62;
  --committed:#2e7d4f; --committed-bg:#e3f2e8;
  --triaged:#2f5f9e; --triaged-bg:#e4ecf7;
  --parked:#9a6a12; --parked-bg:#f6ecd8;
  --dropped:#7a7f7d; --dropped-bg:#ebedec;
  --inbox:#8a3fa0; --inbox-bg:#f1e5f5;
  --display:"Space Grotesk",system-ui,sans-serif; --body:"IBM Plex Sans",system-ui,sans-serif; --mono:"IBM Plex Mono",ui-monospace,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#141917; --surface:#1c2220; --fg:#e4e8e6; --muted:#97a29d; --line:#2c3431; --accent:#6fc2ad;
  --committed:#6fcf97; --committed-bg:#1d3326; --triaged:#8db4ec; --triaged-bg:#1d2a3d;
  --parked:#e3b55a; --parked-bg:#3a2f1a; --dropped:#9aa19e; --dropped-bg:#272d2b; --inbox:#d39be6; --inbox-bg:#33223a; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#141917; --surface:#1c2220; --fg:#e4e8e6; --muted:#97a29d; --line:#2c3431; --accent:#6fc2ad;
  --committed:#6fcf97; --committed-bg:#1d3326; --triaged:#8db4ec; --triaged-bg:#1d2a3d;
  --parked:#e3b55a; --parked-bg:#3a2f1a; --dropped:#9aa19e; --dropped-bg:#272d2b; --inbox:#d39be6; --inbox-bg:#33223a; color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:15px;line-height:1.5}
.wrap{max-width:1100px;margin:0 auto;padding-block:28px 60px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:22px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 20px}
h1{font-family:var(--display);font-weight:600;font-size:1.9rem;margin:0;letter-spacing:-.01em}
.hd{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.src{font-family:var(--mono);font-size:12px;color:var(--muted)}
.theme{font:inherit;font-size:12px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:8px;padding:4px 10px;cursor:pointer}
.stats{display:flex;flex-wrap:wrap;gap:8px}
.chip{font:inherit;font-size:13px;display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}
.chip b{font-family:var(--mono);font-weight:500;font-variant-numeric:tabular-nums}
.chip .dot{width:8px;height:8px;border-radius:50%}
.chip[aria-pressed="true"]{border-color:var(--fg);box-shadow:inset 0 0 0 1px var(--fg)}
.chip:focus-visible,.row:focus-visible,input:focus-visible,select:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tools{display:flex;flex-wrap:wrap;gap:10px}
.tools input,.tools select{font:inherit;font-size:14px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg)}
.tools input{flex:1 1 240px;min-width:0}
details.notes{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 16px}
details.notes summary{cursor:pointer;font-weight:600;font-size:14px}
details.notes .md{margin-top:8px}
#list{display:grid;gap:18px}
.group{display:grid;gap:6px}
.group h2{font-family:var(--display);font-weight:500;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:6px 0 2px;display:flex;gap:8px;align-items:center}
.group h2 span{font-family:var(--mono);letter-spacing:0}
.row{display:grid;grid-template-columns:auto 1fr auto;gap:4px 14px;align-items:start;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;cursor:pointer;text-align:left;font:inherit;color:inherit;width:100%}
.row:hover{border-color:var(--muted)}
.row .t{font-weight:600;min-width:0}
.row .s{grid-column:2/4;color:var(--muted);font-size:13.5px;min-width:0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.row .m{font-family:var(--mono);font-size:12px;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
.pill{font-family:var(--mono);font-size:11.5px;padding:2px 8px;border-radius:999px;white-space:nowrap;text-transform:lowercase;color:var(--dropped);background:var(--dropped-bg)}
.st-committed{color:var(--committed);background:var(--committed-bg)} .st-triaged{color:var(--triaged);background:var(--triaged-bg)}
.st-parked{color:var(--parked);background:var(--parked-bg)} .st-dropped{color:var(--dropped);background:var(--dropped-bg)}
.st-inbox,.st-shaping,.st-shaped{color:var(--inbox);background:var(--inbox-bg)}
.app{font-family:var(--mono);font-size:11.5px;color:var(--muted);border:1px solid var(--line);padding:1px 7px;border-radius:999px}
.empty{color:var(--muted);padding:24px;text-align:center}
.scrim{position:fixed;inset:0;background:rgb(0 0 0 / .35);z-index:20}
.pane{position:fixed;top:0;right:0;bottom:0;width:min(640px,100%);background:var(--surface);border-left:1px solid var(--line);z-index:21;overflow-y:auto;
  padding-top:calc(env(safe-area-inset-top,0px) + 20px);padding-bottom:calc(env(safe-area-inset-bottom,0px) + 40px);padding-left:24px;padding-right:max(24px,env(safe-area-inset-right,0px))}
[hidden]{display:none!important}
.pane .close{position:sticky;top:0;float:right;font:inherit;font-size:13px;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:8px;padding:6px 12px;cursor:pointer}
.pane h3{font-family:var(--display);font-weight:600;font-size:1.4rem;margin:4px 0 10px;text-wrap:balance;max-width:90%}
.meta{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13px;margin:0 0 16px}
.meta dt{color:var(--muted)} .meta dd{margin:0;font-family:var(--mono);font-size:12.5px;min-width:0;overflow-wrap:anywhere}
.md{font-size:14.5px;max-width:65ch;overflow-wrap:anywhere}
.md p{margin:.5em 0} .md ul,.md ol{padding-left:1.2em;margin:.4em 0}
.md h4,.md h5,.md h6{font-family:var(--display);font-size:1rem;margin:1em 0 .3em}
.md blockquote{margin:.5em 0;padding-left:12px;border-left:3px solid var(--line);color:var(--muted)}
.md table{border-collapse:collapse;display:block;overflow-x:auto} .md th,.md td{border:1px solid var(--line);padding:4px 8px;text-align:left}
.md code{font-family:var(--mono);font-size:.88em;background:var(--bg);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}
.md a{color:var(--accent)}
.log{margin-top:20px;border-top:1px solid var(--line);padding-top:12px}
.log h4{font-family:var(--display);font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 8px}
.log .md{font-size:13px}
@media (max-width:560px){.row{grid-template-columns:1fr auto}.row .pill{grid-row:1;grid-column:2}.row .t{grid-column:1}.row .m{grid-column:1/3}.row .s{grid-column:1/3}.pane{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
@media (prefers-reduced-motion:no-preference){.pane{animation:slide .18s ease-out}@keyframes slide{from{transform:translateX(24px);opacity:.6}}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Kairyn Backlog</h1>
    <div class="hd"><span class="src">%SOURCE%</span><button class="theme" id="theme" type="button">Theme: auto</button></div>
  </header>
  <div class="stats" id="stats"></div>
  <div class="tools">
    <input id="q" type="search" placeholder="Search titles, problems, notes" aria-label="Search">
    <select id="app" aria-label="Appetite"><option value="">Any appetite</option>%APPETITES%<option value="none">Not set</option></select>
  </div>
  <details class="notes"><summary>Triage notes (Next and Parked, from TRIAGE.md)</summary><div class="md">%NOTES%</div></details>
  <div id="list"></div>
</div>
<div class="scrim" id="scrim" hidden></div>
<aside class="pane" id="pane" hidden aria-modal="true" role="dialog"></aside>
<script>
const DATA=%DATA%;
const ORDER=%ORDER%;
const DOT={committed:"--committed",triaged:"--triaged",parked:"--parked",dropped:"--dropped",inbox:"--inbox",shaping:"--inbox",shaped:"--inbox"};
const label=s=>s?s[0].toUpperCase()+s.slice(1):"No status";
const bySlug=Object.fromEntries(DATA.map(d=>[d.slug,d]));
const active=new Set();
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const cls=s=>"st-"+String(s).replace(/[^\w-]/g,"");
function renderStats(){
  const counts={};DATA.forEach(d=>counts[d.status]=(counts[d.status]||0)+1);
  const el=document.getElementById("stats");
  el.innerHTML=`<button class="chip" data-s="" aria-pressed="${active.size===0}">All <b>${DATA.length}</b></button>`+
    ORDER.filter(s=>counts[s]).map(s=>`<button class="chip" data-s="${esc(s)}" aria-pressed="${active.has(s)}"><span class="dot" style="background:var(${DOT[s]||"--dropped"})"></span>${esc(label(s))} <b>${counts[s]}</b></button>`).join("");
  el.querySelectorAll(".chip").forEach(b=>b.onclick=()=>{const s=b.dataset.s;if(!s)active.clear();else active.has(s)?active.delete(s):active.add(s);renderStats();renderList()});
}
function renderList(){
  const q=document.getElementById("q").value.trim().toLowerCase();
  const ap=document.getElementById("app").value;
  const items=DATA.filter(d=>(!active.size||active.has(d.status))&&(!ap||(ap==="none"?!d.appetite:d.appetite===ap))&&(!q||(d.title+" "+d.slug+" "+d.body).toLowerCase().includes(q)));
  const list=document.getElementById("list");
  if(!items.length){list.innerHTML=`<div class="empty">No ideas match. Clear the search or pick another status.</div>`;return}
  list.innerHTML=ORDER.map(s=>{
    const g=items.filter(d=>d.status===s).sort((a,b)=>b.file.localeCompare(a.file));
    if(!g.length)return"";
    return `<section class="group"><h2>${esc(label(s))} <span>${g.length}</span></h2>`+g.map(d=>
      `<button class="row" data-slug="${esc(d.slug)}"><span class="pill ${cls(d.status)}">${esc(d.status||"none")}</span><span class="t">${esc(d.title)}</span><span class="m">${d.appetite?`<span class="app">${esc(d.appetite)}</span> `:""}${esc(d.date)}</span><span class="s">${esc(d.summary)||"&nbsp;"}</span></button>`).join("")+`</section>`;
  }).join("");
  list.querySelectorAll(".row").forEach(r=>r.onclick=()=>{location.hash=r.dataset.slug});
}
let opener=null;
function openPane(slug){
  const d=bySlug[slug],pane=document.getElementById("pane"),scrim=document.getElementById("scrim");
  if(!d){pane.hidden=true;scrim.hidden=true;if(opener){opener.focus();opener=null}return}
  if(pane.hidden)opener=document.activeElement;
  pane.innerHTML=`<button class="close" id="close" type="button">Close</button>
    <span class="pill ${cls(d.status)}">${esc(d.status||"none")}</span>
    <h3>${esc(d.title)}</h3>
    <dl class="meta"><dt>Appetite</dt><dd>${esc(d.appetite||"not set")}</dd><dt>Captured</dt><dd>${esc(d.date||"—")}</dd><dt>Review by</dt><dd>${esc(d.review_by||"—")}</dd><dt>Requester</dt><dd>${esc(d.requester||"—")}</dd><dt>File</dt><dd><a href="${esc(d.file)}">docs/backlog/${esc(d.file)}</a></dd></dl>
    <div class="md">${d.body_html}</div>
    ${d.log_html?`<div class="log"><h4>Log</h4><div class="md">${d.log_html}</div></div>`:""}`;
  pane.hidden=false;scrim.hidden=false;pane.scrollTop=0;
  document.getElementById("close").onclick=closePane;document.getElementById("close").focus();
}
function closePane(){history.replaceState(null,"",location.pathname+location.search);openPane(null)}
document.getElementById("scrim").onclick=closePane;
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!document.getElementById("pane").hidden)closePane()});
window.addEventListener("hashchange",()=>openPane(decodeURIComponent(location.hash.slice(1))));
document.getElementById("q").oninput=renderList;
document.getElementById("app").onchange=renderList;
const THEMES=["auto","light","dark"],themeBtn=document.getElementById("theme");
function setTheme(t){
  if(t==="auto")document.documentElement.removeAttribute("data-theme");else document.documentElement.dataset.theme=t;
  themeBtn.textContent="Theme: "+t;
  try{localStorage.setItem("kairyn-backlog-theme",t)}catch(e){}
}
themeBtn.onclick=()=>setTheme(THEMES[(THEMES.indexOf(themeBtn.textContent.slice(7))+1)%3]);
let saved="auto";try{saved=localStorage.getItem("kairyn-backlog-theme")||"auto"}catch(e){}
setTheme(THEMES.includes(saved)?saved:"auto");
renderStats();renderList();
if(location.hash)openPane(decodeURIComponent(location.hash.slice(1)));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
