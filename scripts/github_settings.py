#!/usr/bin/env python3
"""Apply or check the GitHub settings that are not in git (R1 to R5, R8).

main: pull request with 0 approvals, the REQUIRED_CHECKS, admins included,
no force push, no deletion. Repo: Dependabot alerts and security updates,
private vulnerability reporting. tests/test_github_settings.py ties
REQUIRED_CHECKS to the job names in ci.yml, so a renamed job fails a test
before it blocks every merge.

Needs `gh` with admin rights on the repo.

Usage (from the repo root):
    python3 scripts/github_settings.py --check   # exit 1 on a difference
    python3 scripts/github_settings.py --apply   # change the live settings
"""
import json
import subprocess
import sys

REPO = "jisundr/kairyn"
BRANCH = "main"
REQUIRED_CHECKS = (
    "tests (ubuntu-latest)",
    "tests (macos-latest)",
    "consumer install (plain python3 3.9)",
    "consumer install (plain python3 3.13)",
    "version-bump",
    "shellcheck",
)


def protection_payload() -> dict:
    """The body of PUT repos/{repo}/branches/{branch}/protection."""
    return {
        "required_status_checks": {"strict": False, "contexts": list(REQUIRED_CHECKS)},
        "enforce_admins": True,
        "required_pull_request_reviews": {"required_approving_review_count": 0},
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }


def _enabled(data: dict, key: str):
    return (data.get(key) or {}).get("enabled")


def protection_problems(data) -> list:
    """Differences between a GET of the branch protection and protection_payload()."""
    if not data:
        return [f"{BRANCH} has no branch protection"]
    problems = []
    reviews = data.get("required_pull_request_reviews")
    if not reviews:
        problems.append("pull requests are not required")
    elif reviews.get("required_approving_review_count") != 0:
        problems.append(f"required approvals is {reviews.get('required_approving_review_count')}, not 0")
    contexts = sorted((data.get("required_status_checks") or {}).get("contexts") or [])
    if contexts != sorted(REQUIRED_CHECKS):
        problems.append(f"required checks are {contexts}, not {sorted(REQUIRED_CHECKS)}")
    if _enabled(data, "enforce_admins") is not True:
        problems.append("protection does not apply to admins")
    if _enabled(data, "allow_force_pushes") is not False:
        problems.append("force pushes are allowed")
    if _enabled(data, "allow_deletions") is not False:
        problems.append("deletion is allowed")
    return problems


def repo_problems(repo: dict, alerts_on: bool, reporting: dict) -> list:
    """Differences in the repo's Dependabot and vulnerability reporting settings."""
    problems = []
    updates = (repo.get("security_and_analysis") or {}).get("dependabot_security_updates") or {}
    if updates.get("status") != "enabled":
        problems.append("Dependabot security updates are off")
    if not alerts_on:
        problems.append("Dependabot alerts are off")
    if not (reporting or {}).get("enabled"):
        problems.append("private vulnerability reporting is off")
    return problems


def _gh(*args: str, body=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh", "api", *args],
        input=None if body is None else json.dumps(body),
        capture_output=True,
        text=True,
    )


def _get_json(path: str):
    result = _gh(path)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout or "null")


def check() -> int:
    protection = _get_json(f"repos/{REPO}/branches/{BRANCH}/protection")
    repo = _get_json(f"repos/{REPO}") or {}
    alerts_on = _gh(f"repos/{REPO}/vulnerability-alerts").returncode == 0
    reporting = _get_json(f"repos/{REPO}/private-vulnerability-reporting") or {}
    problems = protection_problems(protection) + repo_problems(repo, alerts_on, reporting)
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        print(f"OK {REPO} settings match")
    return 1 if problems else 0


def apply() -> int:
    calls = [
        (["-X", "PUT", f"repos/{REPO}/branches/{BRANCH}/protection", "--input", "-"], protection_payload()),
        (["-X", "PUT", f"repos/{REPO}/vulnerability-alerts"], None),
        (["-X", "PUT", f"repos/{REPO}/automated-security-fixes"], None),
        (["-X", "PUT", f"repos/{REPO}/private-vulnerability-reporting"], None),
    ]
    for args, body in calls:
        result = _gh(*args, body=body)
        if result.returncode != 0:
            print(f"FAIL gh api {' '.join(args)}: {result.stderr.strip()}")
            return 1
    return check()


def main(argv: list) -> int:
    if argv == ["--check"]:
        return check()
    if argv == ["--apply"]:
        return apply()
    print("usage: github_settings.py --check | --apply", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
