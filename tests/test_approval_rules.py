"""The design and requirements stages share one set of approval rules in _approval.md (split-design-stage slice)."""
from helpers import PLUGIN

APPROVAL = PLUGIN / "stages" / "_approval.md"
GATED = ("DESIGN", "REQUIREMENTS")
LINE = 'Approval: <git config user.name>, <timestamp>, "<the user\'s words>"'


def _update(stage):
    return (PLUGIN / "stages" / f"{stage}.md").read_text().split("## State update", 1)[1].split("\n## ", 1)[0]


def test_approval_rules_live_in_one_shared_file():
    text = APPROVAL.read_text()
    for rule in ("`Approval: pending`", "`status: blocked`", "Never approve for the user", LINE):
        assert rule in text, rule


def test_gated_stages_read_the_shared_rules_and_do_not_repeat_them():
    for stage in GATED:
        update = _update(stage)
        assert "`_approval.md`" in update, stage
        for rule in ("Never approve for the user", LINE, "`status: blocked`"):
            assert rule not in update, f"{stage} repeats {rule!r}"


def test_the_shared_file_is_not_a_stage():
    """Like _template.md: no stage front matter, so the stage list and STATE.md skip it."""
    assert not APPROVAL.read_text().startswith("---")
