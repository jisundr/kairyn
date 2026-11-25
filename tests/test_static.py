"""Static checks on the plugin's own files."""
import json

import pytest
import yaml

from helpers import PLUGIN, ROOT, VERIFY, split_front_matter

STAGES = sorted(p for p in (PLUGIN / "stages").glob("*.md") if not p.name.startswith("_"))
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


# --- commands -----------------------------------------------------------------

import re

COMMANDS = sorted((PLUGIN / "commands").glob("*.md"))


def test_expected_commands_exist():
    assert {c.stem for c in COMMANDS} >= {"init", "check"}


@pytest.mark.parametrize("command", COMMANDS, ids=lambda p: p.stem)
def test_command_has_description_and_valid_script_references(command):
    text = command.read_text()
    fm, _ = split_front_matter(text)
    assert yaml.safe_load(fm).get("description")
    for script in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/(scripts/[\w.-]+)", text):
        assert (PLUGIN / script).is_file(), f"{command.name} references missing {script}"



def test_state_template_lists_the_afk_stages_after_design():
    """Design is required after requirements (ADR 0006); build, gates and review follow it (D6)."""
    data = yaml.safe_load(split_front_matter((PLUGIN / "templates" / "STATE.md").read_text())[0])
    assert list(data["stages"]) == ["requirements", "design", "build", "gates", "review"]
    assert set(data["stages"].values()) == {"pending"}


def test_design_approval_hands_off_to_build():
    """D5: design approval starts the AFK run."""
    update = (PLUGIN / "stages" / "DESIGN.md").read_text().split("## State update", 1)[1]
    assert "`stage: build`" in update and "status: done" not in update


def test_design_cuts_vertical_slices():
    """D13: T1 is the tracer bullet; each T<n> has an end-to-end done command and after: blockers."""
    steps = (PLUGIN / "stages" / "DESIGN.md").read_text().split("## Steps", 1)[1].split("\n## ", 1)[0]
    for word in ("tracer bullet", "after:", "Done: `"):
        assert word in steps, word


def test_afk_stages_follow_design_in_order():
    orders = [yaml.safe_load(split_front_matter((PLUGIN / "stages" / f"{s}.md").read_text())[0])["order"]
              for s in ("DESIGN", "BUILD", "GATES", "REVIEW")]
    assert orders == sorted(orders) == [2, 3, 4, 5]


def test_requirements_hands_off_to_design():
    text = (PLUGIN / "stages" / "REQUIREMENTS.md").read_text()
    assert "`stage: design`" in text.split("## State update", 1)[1]


def test_design_stage_is_required_and_follows_requirements():
    data = yaml.safe_load(split_front_matter((PLUGIN / "stages" / "DESIGN.md").read_text())[0])
    assert data["order"] == 2 and not data.get("optional")


def test_design_checks_requirements_approval_first():
    """R6: no design before the requirements are approved."""
    steps = (PLUGIN / "stages" / "DESIGN.md").read_text().split("## Steps", 1)[1]
    first = next(line for line in steps.splitlines() if line.startswith("1."))
    assert "Approval" in first


def test_docs_name_the_design_stage():
    for doc in (ROOT / "README.md", PLUGIN / "harness" / ".harness" / "workflows" / "running-stages.md"):
        assert "/kairyn:design" in doc.read_text(), doc


def test_concept_template_has_the_sections_the_grill_check_needs():
    """Grill wrote `# Concept` 2 in 10 times without a template (run 20261123T083521Z)."""
    import re

    from checks import CONCEPT_SECTIONS
    text = (PLUGIN / "templates" / "CONCEPT.md").read_text()
    data = yaml.safe_load(split_front_matter(text)[0])
    assert set(data) == {"task", "stage", "summary"} and data["stage"] == "grill"
    headings = [h.lower() for h in re.findall(r"^## (.+)$", text, re.M)]
    assert headings == list(CONCEPT_SECTIONS)


def test_grill_output_points_to_the_concept_template():
    text = (PLUGIN / "stages" / "GRILL.md").read_text()
    output = text.split("## Output", 1)[1].split("\n## ", 1)[0]
    assert ".kairyn/templates/CONCEPT.md" in output


# --- the close stage (R4, R5) -------------------------------------------------

# A bare /exit is the Claude Code built-in, so no shipped or tested file names the stage exit.  # old-name
STAGE_WORD = re.compile(r"(?<![A-Za-z_])exits?(?![A-Za-z])", re.I)  # old-name
# Process exit codes and `## Exit criteria` keep the word (A1).
CODE_USES = re.compile(r"sys\.exit|SystemExit|Exit criteria|exits? (with )?code|exits? ([0-9]|\{|non-zero)|exit \"\$"  # old-name
                       r"|exit \((not )?0\)|exit=|\| Exit \||(red|green|other) exit|\"exit\":|exit: skipped", re.I)  # old-name
# History keeps the old name. JSON has no comments, so the whole file is allowed.
HISTORY_FILES = {"plugin/release-hashes.json"}
# A test that checks the old name is gone marks each such line, so the rest of the file stays guarded.
OLD_NAME_MARK = "# old-name"
MARK_FILES = {"tests/test_static.py", "tests/test_skills.py", "tests/test_upgrade.py", "tests/test_dev_harness.py"}


def _guarded_files():
    roots = [PLUGIN, ROOT / "tests", ROOT / "evals" / "promptfoo", ROOT / "README.md", *(ROOT / "evals").glob("*.py")]
    for root in roots:
        for path in ([root] if root.is_file() else sorted(root.rglob("*"))):
            rel = path.relative_to(ROOT).as_posix()
            if path.is_file() and "__pycache__" not in rel and rel not in HISTORY_FILES:
                yield rel, path


def _guarded_lines():
    for rel, path in _guarded_files():
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            yield rel, n, line


def test_no_shipped_or_tested_file_names_the_exit_stage():
    hits = [f"{rel}:{n}: {line.strip()[:100]}" for rel, n, line in _guarded_lines()
            if not (rel in MARK_FILES and line.rstrip().endswith(OLD_NAME_MARK))
            and STAGE_WORD.search(CODE_USES.sub("", line))]
    assert not hits, "\n".join(hits)


def test_only_the_old_name_tests_mark_lines():
    marked = sorted({rel for rel, _, line in _guarded_lines() if OLD_NAME_MARK in line} - MARK_FILES)
    assert marked == []


def test_close_stage_tags_its_lines_close():
    text = (PLUGIN / "stages" / "CLOSE.md").read_text()
    assert "[close]" in text and "[exit]" not in text  # old-name


def test_close_eval_replaces_the_exit_eval():
    assert (ROOT / "evals" / "promptfoo" / "close.yaml").is_file()
    assert not (ROOT / "evals" / "promptfoo" / "exit.yaml").exists()  # old-name


def test_no_noqa_in_promptfoo_evals():
    """No new escape hatch in evals/promptfoo/: no linter runs there, and feat(T3) of skill-names-clash added
    two that no reviewer justified."""
    files = sorted(p for p in (ROOT / "evals" / "promptfoo").rglob("*") if p.suffix in (".py", ".yaml"))
    hits = [f"{p.name}:{i}" for p in files for i, line in enumerate(p.read_text().splitlines(), 1) if "noqa" in line]
    assert hits == [], f"remove `# noqa` from {hits}"
