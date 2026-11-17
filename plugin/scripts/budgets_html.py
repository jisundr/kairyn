#!/usr/bin/env python3
"""Render .harness/budgets.yml plus current file sizes as a self-contained HTML page for people.

The page is built from the same data the tests enforce, so it cannot drift from it.

Usage:
    python budgets_html.py [--root DIR] [--out PATH]    # default: .harness/budgets.html (git-ignored)
"""
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from budgets import Budget, budget_for, estimate_tokens, find_docs, load_config, root_from_args

CLASS_LABELS = {
    "always": ("Always loaded", "in every session"),
    "on-demand": ("On demand", "read when the task matches"),
    "runtime": ("Runtime", "read when a command or stage runs"),
}

CSS = """
:root{--bg:#fbfaf8;--card:#fff;--text:#1f1d1a;--muted:#6b665e;--line:#e6e2db;--bar:#d9d4ca;
--ok:#2f7d5b;--warn:#b7791f;--bad:#c0392b;--always:#7c4dbd;--on-demand:#2b6cb0;--runtime:#a0612a}
@media (prefers-color-scheme: dark){:root{--bg:#161513;--card:#1f1d1a;--text:#ece8e1;--muted:#a09a90;
--line:#34312c;--bar:#3a3731;--ok:#5cc49a;--warn:#e0a94a;--bad:#ef7a6b;--always:#b494e8;--on-demand:#7fb2e8;--runtime:#d99a62}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:960px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:16px;margin:32px 0 12px}
.sub{color:var(--muted);margin:0 0 24px;font-size:14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card b{display:block;font-size:22px}.card span{color:var(--muted);font-size:13px}
.card .cls{font-weight:600;font-size:14px}
.table{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:560px}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line);font-size:14px}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
code{font:13px ui-monospace,SFMono-Regular,Menlo,monospace}
.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.chip{display:inline-block;white-space:nowrap;padding:1px 8px;border-radius:99px;font-size:12px;border:1px solid currentColor}
.always{color:var(--always)}.on-demand{color:var(--on-demand)}.runtime{color:var(--runtime)}
.meter{width:140px;height:8px;background:var(--bar);border-radius:4px;overflow:hidden}
.meter i{display:block;height:100%;background:var(--ok)}
.warn .meter i{background:var(--warn)}.over .meter i{background:var(--bad)}
.over td.status{color:var(--bad);font-weight:600}.warn td.status{color:var(--warn)}
td.status{color:var(--muted);white-space:nowrap}
ol{margin:0;padding:0 0 0 20px}li{margin:4px 0}
footer{color:var(--muted);font-size:13px;margin-top:32px}
"""


def _row(rel: str, used: int, budget: Budget | None) -> tuple[float, str]:
    name = f"<code>{escape(rel)}</code>"
    if budget is None:
        return float("inf"), (f'<tr class="over"><td>{name}</td><td>-</td><td class="num">{used} / -</td>'
                              '<td></td><td class="status">no budget</td></tr>')
    pct = used / budget.max_tokens
    state = "over" if pct > 1 else "warn" if pct >= 0.85 else ""
    status = f"over by {used - budget.max_tokens}" if pct > 1 else f"{budget.max_tokens - used} left"
    chip = f'<span class="chip {budget.load}">{escape(budget.load)}</span>'
    meter = f'<div class="meter"><i style="width:{min(pct, 1) * 100:.0f}%"></i></div>'
    cls = f' class="{state}"' if state else ""
    return pct, (f"<tr{cls}><td>{name}</td><td>{chip}</td><td class=\"num\">{used} / {budget.max_tokens}</td>"
                 f'<td>{meter}</td><td class="status">{status}</td></tr>')


def render_html(root: Path, budgets: list[Budget], generated: datetime | None = None, strict: bool = True) -> str:
    generated = generated or datetime.now(timezone.utc)
    rows, totals = [], {c: [0, 0, 0] for c in CLASS_LABELS}   # used, budget, files
    for rel in find_docs(root):
        budget = budget_for(rel, budgets)
        if budget is None and not strict:
            continue
        used = estimate_tokens((root / rel).read_text())
        rows.append(_row(rel, used, budget))
        if budget:
            t = totals[budget.load]
            t[0] += used
            t[1] += budget.max_tokens
            t[2] += 1
    rows.sort(key=lambda r: -r[0])

    cards = "".join(
        f'<div class="card"><span class="cls {cls}">{label}</span><b>{used}</b>'
        f"<span>of {limit} tokens, {files} file{'s' if files != 1 else ''}<br>{escape(hint)}</span></div>"
        for cls, (label, hint) in CLASS_LABELS.items()
        for used, limit, files in [totals[cls]]
    )
    rules = "".join(
        f'<li><code>{escape(b.pattern)}</code> &rarr; {b.max_tokens} tokens, '
        f'<span class="chip {b.load}">{escape(b.load)}</span></li>'
        for b in budgets
    )
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>kairyn file budgets</title><style>{CSS}</style></head><body><main>"
        "<h1>File budgets</h1>"
        "<p class=\"sub\">How much of each markdown file an AI has to read, against the limit we set. "
        "Sizes are estimated tokens (characters &divide; 4).</p>"
        f'<div class="cards">{cards}</div>'
        "<h2>Files, most used first</h2>"
        '<div class="table"><table><thead><tr><th>File</th><th>Load</th><th>Tokens</th><th>Usage</th><th></th></tr></thead>'
        f"<tbody>{''.join(r for _, r in rows)}</tbody></table></div>"
        "<h2>Budget rules</h2>"
        f"<ol>{rules}</ol><p class=\"sub\">Checked top to bottom: first match wins.</p>"
        f"<footer>Generated from <code>.harness/budgets.yml</code> and the current files, "
        f"{generated:%Y-%m-%d %H:%M} UTC. Change limits in the YAML, then regenerate.</footer>"
        "</main></body></html>\n"
    )


def write_html(root: Path, budgets: list[Budget], out: Path, generated: datetime | None = None, strict: bool = True) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(root, budgets, generated, strict))


def main(argv: list[str]) -> int:
    root = root_from_args(argv)
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else root / ".harness" / "budgets.html"
    budgets, strict = load_config(root / ".harness" / "budgets.yml")
    write_html(root, budgets, out, strict=strict)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
