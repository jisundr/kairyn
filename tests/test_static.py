"""Static checks on the plugin's own files."""
import json

import pytest
import yaml

from helpers import PLUGIN, ROOT, VERIFY, split_front_matter

STAGES = sorted(p for p in (PLUGIN / "stages").glob("*.md") if p.name != "_template.md")
REQUIRED_SECTIONS = ["## Inputs", "## Steps", "## Output", "## Exit criteria", "## State update", "## Learnings"]


def test_manifests_are_valid_json():
    for path in (PLUGIN / ".claude-plugin" / "plugin.json", ROOT / ".claude-plugin" / "marketplace.json"):
        json.loads(path.read_text())


def test_init_command_calls_verifier():
    text = (PLUGIN / "commands" / "init.md").read_text()
    assert "scripts/verify-init.sh" in text
    assert VERIFY.exists()


def test_stages_exist():
    assert STAGES, "no stage definitions found"


@pytest.mark.parametrize("stage", STAGES, ids=lambda p: p.stem)
def test_stage_front_matter(stage):
    fm, _ = split_front_matter(stage.read_text())
    data = yaml.safe_load(fm)
    assert data["name"] == stage.stem.lower()
    assert isinstance(data["order"], int)
    assert data["purpose"]


@pytest.mark.parametrize("stage", STAGES, ids=lambda p: p.stem)
def test_stage_sections(stage):
    lines = stage.read_text().splitlines()
    for section in REQUIRED_SECTIONS:
        assert section in lines, f"{stage.name} missing {section!r}"


def test_stage_orders_are_unique():
    orders = [yaml.safe_load(split_front_matter(s.read_text())[0])["order"] for s in STAGES]
    assert len(orders) == len(set(orders))


def test_state_template_front_matter():
    fm, body = split_front_matter((PLUGIN / "templates" / "STATE.md").read_text())
    # Placeholders like <slug> are valid YAML strings once quoted by the loader.
    data = yaml.safe_load(fm)
    assert set(data) == {"task", "title", "stage", "status", "stages", "created", "updated"}
    assert data["stage"] in data["stages"]
    assert "# Log" in body.splitlines()
