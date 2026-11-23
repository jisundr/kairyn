"""scripts/github_settings.py: GitHub settings for main as code (R1 to R5, R8; K1)."""
import itertools
import re
import sys

import yaml

from helpers import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from github_settings import (  # noqa: E402
    REQUIRED_CHECKS,
    protection_payload,
    protection_problems,
    repo_problems,
)

CI = ROOT / ".github" / "workflows" / "ci.yml"
MATRIX_REF = re.compile(r"\$\{\{\s*matrix\.(\w+)\s*\}\}")


def ci_check_names():
    """The check name each ci.yml job reports, with its matrix expanded."""
    names = []
    for key, job in yaml.safe_load(CI.read_text())["jobs"].items():
        template = job.get("name", key)
        matrix = job.get("strategy", {}).get("matrix", {})
        axes = MATRIX_REF.findall(template)
        for values in itertools.product(*(matrix[a] for a in axes)):
            name = template
            for axis, value in zip(axes, values):
                name = re.sub(r"\$\{\{\s*matrix\." + axis + r"\s*\}\}", str(value), name)
            names.append(name)
    return names


def test_required_checks_are_the_six_in_r2():
    assert sorted(REQUIRED_CHECKS) == sorted([
        "tests (ubuntu-latest)",
        "tests (macos-latest)",
        "consumer install (plain python3 3.9)",
        "consumer install (plain python3 3.13)",
        "shellcheck",
        "version-bump",
    ])


def test_required_checks_equal_ci_job_names():
    assert sorted(REQUIRED_CHECKS) == sorted(ci_check_names())


def test_payload_needs_a_pull_request_with_zero_approvals():
    reviews = protection_payload()["required_pull_request_reviews"]
    assert reviews["required_approving_review_count"] == 0


def test_payload_requires_exactly_the_checks():
    checks = protection_payload()["required_status_checks"]
    assert sorted(checks["contexts"]) == sorted(REQUIRED_CHECKS)


def test_payload_includes_admins_and_blocks_force_push_and_deletion():
    payload = protection_payload()
    assert payload["enforce_admins"] is True
    assert payload["allow_force_pushes"] is False
    assert payload["allow_deletions"] is False


def readback(**overrides):
    """What GET branches/main/protection returns when the payload was applied."""
    data = {
        "required_pull_request_reviews": {"required_approving_review_count": 0},
        "required_status_checks": {"contexts": list(REQUIRED_CHECKS)},
        "enforce_admins": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
    }
    data.update(overrides)
    return data


def test_applied_protection_has_no_problems():
    assert protection_problems(readback()) == []


def test_missing_protection_is_a_problem():
    assert protection_problems(None)


def test_each_protection_difference_is_a_problem():
    bad = [
        readback(required_pull_request_reviews=None),
        readback(required_pull_request_reviews={"required_approving_review_count": 1}),
        readback(required_status_checks={"contexts": list(REQUIRED_CHECKS)[:-1]}),
        readback(required_status_checks={"contexts": [*REQUIRED_CHECKS, "extra"]}),
        readback(enforce_admins={"enabled": False}),
        readback(allow_force_pushes={"enabled": True}),
        readback(allow_deletions={"enabled": True}),
    ]
    for data in bad:
        assert protection_problems(data), data


def test_repo_settings_on_have_no_problems():
    repo = {"security_and_analysis": {"dependabot_security_updates": {"status": "enabled"}}}
    assert repo_problems(repo, alerts_on=True, reporting={"enabled": True}) == []


def test_each_repo_setting_off_is_a_problem():
    on = {"security_and_analysis": {"dependabot_security_updates": {"status": "enabled"}}}
    off = {"security_and_analysis": {"dependabot_security_updates": {"status": "disabled"}}}
    assert repo_problems(off, alerts_on=True, reporting={"enabled": True})
    assert repo_problems({}, alerts_on=True, reporting={"enabled": True})
    assert repo_problems(on, alerts_on=False, reporting={"enabled": True})
    assert repo_problems(on, alerts_on=True, reporting={"enabled": False})
