"""The shipped checkers use only the standard library. Their tiny parser must agree with PyYAML."""
from pathlib import Path

import pytest
import yaml

from helpers import ROOT
from simple_yaml import parse_budgets, parse_front_matter

HEADERS = [
    '---\ntitle: Init\nsummary: "How /kairyn:init works, and the rule."\nread_when: "changing init"\nload: on-demand\n---\n\n# x\n',
    "---\ntitle: 'Quoted: with colon'\nsummary: plain text\nread_when: x\nload: always\n---\nbody\n",
]


@pytest.mark.parametrize("text", HEADERS)
def test_front_matter_matches_pyyaml(text):
    expected = yaml.safe_load(text.split("---\n")[1])
    assert parse_front_matter(text) == expected


def test_no_front_matter_is_none():
    assert parse_front_matter("# just a heading\n") is None


def test_unterminated_front_matter_is_none():
    assert parse_front_matter("---\ntitle: x\n") is None


def test_front_matter_with_nested_structure_is_rejected():
    assert parse_front_matter("---\ntitle: x\nitems:\n  - a\n---\n") is None


def test_budgets_match_pyyaml_on_the_real_file():
    text = (ROOT / ".harness" / "budgets.yml").read_text()
    options, entries = parse_budgets(text)
    assert entries == yaml.safe_load(text)["budgets"]


def test_budgets_options_are_parsed():
    options, entries = parse_budgets("strict: false\nbudgets:\n  - {pattern: a.md, max_tokens: 5, load: always}\n")
    assert options == {"strict": False}
    assert entries == [{"pattern": "a.md", "max_tokens": 5, "load": "always"}]


def test_budgets_default_options_are_empty():
    options, _ = parse_budgets("budgets:\n  - {pattern: a.md, max_tokens: 5, load: always}\n")
    assert options == {}


def test_budgets_ignore_comments_and_blank_lines():
    text = "# note\n\nbudgets:   # inline\n  # another\n  - {pattern: 'a.md', max_tokens: 5, load: always}   # why\n"
    assert parse_budgets(text)[1] == [{"pattern": "a.md", "max_tokens": 5, "load": "always"}]


@pytest.mark.parametrize("bad", [
    "budgets:\n  - not a mapping\n",
    "budgets:\n  - {pattern a.md}\n",
    "nonsense\n",
])
def test_malformed_budgets_raise(bad):
    with pytest.raises(ValueError):
        parse_budgets(bad)
