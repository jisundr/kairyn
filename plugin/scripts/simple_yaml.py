"""A tiny parser for the two YAML shapes the checkers read, so they need only python3.

Supported, and nothing more:
  - front matter: `key: value` lines between `---` fences (values are single-line strings)
  - budgets.yml: optional `key: value` options, then `budgets:` followed by
    `- {pattern: x, max_tokens: 5, load: y}` lines
Comments (`# ...`) and blank lines are ignored. Anything else raises ValueError
(or returns None for front matter), so malformed files fail loudly.
tests/test_simple_yaml.py checks it against PyYAML.
"""
from __future__ import annotations

import re

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _scalar(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def _strip_comment(line: str) -> str:
    """Drop a trailing ` # comment` that is not inside quotes."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i].rstrip()
    return line.rstrip()


def _split_pair(line: str):
    key, sep, value = line.partition(":")
    if not sep or not key.strip() or " " in key.strip():
        raise ValueError(f"expected `key: value`, got {line!r}")
    return key.strip(), value


def parse_front_matter(text: str) -> dict | None:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None
    data = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line[0].isspace() or line.lstrip().startswith("-"):
            return None   # nested structure: not supported
        try:
            key, value = _split_pair(line)
        except ValueError:
            return None
        if not value.strip():
            return None   # `key:` opens a nested block
        data[key] = _scalar(value)
    return data


def parse_budgets(text: str) -> tuple[dict, list[dict]]:
    options, entries, in_budgets = {}, [], False
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_budgets:
                raise ValueError(f"list item before `budgets:`: {raw!r}")
            body = stripped[2:].strip()
            if not (body.startswith("{") and body.endswith("}")):
                raise ValueError(f"budget entries must look like `- {{pattern: x, ...}}`: {raw!r}")
            entry = {}
            for part in body[1:-1].split(","):
                key, value = _split_pair(part)
                entry[key] = _scalar(value)
            entries.append(entry)
            continue
        key, value = _split_pair(stripped)
        if key == "budgets" and not value.strip():
            in_budgets = True
        elif not in_budgets and value.strip():
            options[key] = _scalar(value)
        else:
            raise ValueError(f"unexpected line: {raw!r}")
    return options, entries
