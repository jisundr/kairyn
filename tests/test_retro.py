"""retro.py: the scripted size checks of the retro stage (learnings.md size, whether a move fits its home)."""
import subprocess
import sys

from helpers import PLUGIN

RETRO = PLUGIN / "scripts" / "retro.py"


def run(root, *args):
    return subprocess.run([sys.executable, str(RETRO), *args, "--root", str(root)], capture_output=True, text=True)


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def budgets(root, *lines):
    write(root, ".harness/budgets.yml", "budgets:\n" + "".join(f"  - {line}\n" for line in lines))


def test_size_uses_the_repo_budget(tmp_path):
    budgets(tmp_path, '{pattern: ".kairyn/learnings.md", max_tokens: 100, load: runtime}')
    write(tmp_path, ".kairyn/learnings.md", "x" * 200)
    result = run(tmp_path, "size")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "learnings.md 50/100"


def test_size_falls_back_to_the_built_in_budget(tmp_path):
    write(tmp_path, ".kairyn/learnings.md", "x" * 40)
    assert run(tmp_path, "size").stdout.strip() == "learnings.md 10/2000"


def test_size_with_no_learnings_file(tmp_path):
    assert run(tmp_path, "size").stdout.strip() == "learnings.md 0/2000"


def test_fits_when_the_text_fits(tmp_path):
    budgets(tmp_path, '{pattern: "docs/*.md", max_tokens: 100, load: on-demand}')
    write(tmp_path, "docs/guide.md", "x" * 200)
    assert run(tmp_path, "fits", "docs/guide.md", "--add", "short rule").stdout.strip() == "FITS"


def test_over_names_the_overflow(tmp_path):
    budgets(tmp_path, '{pattern: "docs/*.md", max_tokens: 100, load: on-demand}')
    write(tmp_path, "docs/guide.md", "x" * 396)
    # 396 + newline + 40 = 437 characters -> 110 tokens, 10 over
    assert run(tmp_path, "fits", "docs/guide.md", "--add", "y" * 40).stdout.strip() == "OVER 10"


def test_kairyn_owned_home(tmp_path):
    write(tmp_path, ".harness/workflows/task-lifecycle.md", "# Task lifecycle\n")
    out = run(tmp_path, "fits", ".harness/workflows/task-lifecycle.md", "--add", "rule").stdout.strip()
    assert out == "KAIRYN-OWNED"


def test_kairyn_template_is_kairyn_owned(tmp_path):
    write(tmp_path, ".kairyn/templates/STATE.md", "x")
    assert run(tmp_path, "fits", ".kairyn/templates/STATE.md", "--add", "rule").stdout.strip() == "KAIRYN-OWNED"


def test_repo_owned_stage_uses_the_built_in_budget(tmp_path):
    write(tmp_path, ".kairyn/stages/DESIGN.md", "x" * 1999)  # + newline + 10 = 2010 chars -> 503 tokens
    assert run(tmp_path, "fits", ".kairyn/stages/DESIGN.md", "--add", "y" * 10).stdout.strip() == "OVER 3"


def test_missing_home(tmp_path):
    assert run(tmp_path, "fits", "docs/nope.md", "--add", "rule").stdout.strip() == "MISSING"


def test_home_with_no_budget_fits(tmp_path):
    write(tmp_path, "CLAUDE.md", "# Repo\n")
    assert run(tmp_path, "fits", "CLAUDE.md", "--add", "rule").stdout.strip() == "FITS"
