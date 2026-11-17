"""Apply the selector: skip evals whose dependencies are unchanged since their last pass."""
from pathlib import Path

import pytest

from helpers import ROOT
from runner import DEFAULT_RUNS, PASSED_RECORD, RESULTS, RUNS, SUMMARY
from selector import deps_hash, load_record, needs_run, parse_depends, record_pass, save_record

EVALS_DIR = Path(__file__).parent

_features: dict[str, dict] = {}   # feature name -> {"hash": str, "outcomes": list[str]}
_nodeid_feature: dict[str, str] = {}


def pytest_addoption(parser):
    parser.addoption("--all-evals", action="store_true", help="Run every eval, ignoring the unchanged-since-last-pass record.")


def _feature_of(item):
    """Convention: evals/test_<name>.py exercises evals/features/<name>.feature."""
    path = Path(str(item.fspath))
    if path.parent != EVALS_DIR or not path.name.startswith("test_"):
        return None
    feature = EVALS_DIR / "features" / f"{path.stem.removeprefix('test_')}.feature"
    return feature if feature.exists() else None


def pytest_itemcollected(item):
    if Path(str(item.fspath)).is_relative_to(EVALS_DIR) and _feature_of(item):
        item.add_marker(pytest.mark.eval)


def pytest_collection_modifyitems(config, items):
    record = load_record(PASSED_RECORD)
    force = config.getoption("--all-evals")
    for item in items:
        path = _feature_of(item)
        if path is None:
            continue
        name = path.stem
        current = deps_hash(ROOT, parse_depends(path.read_text()))
        feature = _features.setdefault(name, {"hash": current, "outcomes": []})
        _nodeid_feature[item.nodeid] = name
        if not needs_run(name, current, record, force):
            item.add_marker(pytest.mark.skip(reason=f"{name}: dependencies unchanged since last pass (use --all-evals)"))


def pytest_runtest_logreport(report):
    name = _nodeid_feature.get(report.nodeid)
    if name is None:
        return
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed" and not report.skipped):
        _features[name]["outcomes"].append("passed" if report.passed else "failed")
    elif report.when == "setup" and report.skipped:
        _features[name]["outcomes"].append("skipped")


def pytest_sessionfinish(session):
    """Record a pass only for features where every scenario ran and passed."""
    if RUNS < DEFAULT_RUNS:
        return  # a smoke run with fewer runs must not vouch for the feature
    record = load_record(PASSED_RECORD)
    changed = False
    for name, info in _features.items():
        outcomes = info["outcomes"]
        if outcomes and all(o == "passed" for o in outcomes):
            record = record_pass(record, name, info["hash"])
            changed = True
    if changed:
        save_record(PASSED_RECORD, record)


def pytest_terminal_summary(terminalreporter):
    """One short block per run: a line per check, plus features skipped as unchanged."""
    lines = [f"{feature:<13}{line}" for feature, line in SUMMARY]
    for name, info in _features.items():
        if info["outcomes"] and all(o == "skipped" for o in info["outcomes"]):
            lines.append(f"{name:<13}skipped (dependencies unchanged since last pass)")
    if not lines:
        return
    terminalreporter.section("eval summary")
    for line in lines:
        terminalreporter.write_line(line)
    if SUMMARY:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "summary.md").write_text("\n".join(f"- {line}" for line in lines) + "\n")
