#!/usr/bin/env bash
# Deterministic tests: same input, same result, no LLM involved.
#   1. Plugin static checks (files, front matter, cross-references)
#   2. verify-init.sh accepts a correct layout and rejects broken ones
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
plugin="$root/plugin"
verify="$plugin/scripts/verify-init.sh"
pass=0; failed=0

ok()   { pass=$((pass+1)); echo "  ok   $1"; }
bad()  { failed=$((failed+1)); echo "  FAIL $1"; }
check() { if eval "$2" >/dev/null 2>&1; then ok "$1"; else bad "$1"; fi; }
expect_fail() { if eval "$2" >/dev/null 2>&1; then bad "$1"; else ok "$1"; fi; }

echo "== static plugin checks"
check "plugin.json is valid JSON"      "python3 -m json.tool '$plugin/.claude-plugin/plugin.json'"
check "marketplace.json is valid JSON" "python3 -m json.tool '$root/.claude-plugin/marketplace.json'"
check "init command exists"            "[ -f '$plugin/commands/init.md' ]"
check "init command calls verify-init" "grep -q 'scripts/verify-init.sh' '$plugin/commands/init.md'"
check "verify-init.sh is executable-safe (bash syntax)" "bash -n '$verify'"

for f in "$plugin"/stages/*.md; do
  n="$(basename "$f")"
  [ "$n" = "_template.md" ] && continue
  stage="${n%.md}"
  check "stage $stage: front matter name matches filename" "grep -qx 'name: $stage' '$f'"
  for sec in "## Inputs" "## Steps" "## Output" "## Exit criteria" "## State update" "## Learnings"; do
    check "stage $stage: has '$sec'" "grep -qx '$sec' '$f'"
  done
done

for key in task title stage status stages created updated; do
  check "STATE.md template has front matter key '$key'" "sed -n '2,/^---$/p' '$plugin/templates/STATE.md' | grep -q '^$key:'"
done
check "STATE.md template has '# Log' section" "grep -qx '# Log' '$plugin/templates/STATE.md'"

echo "== verify-init.sh behaviour"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

# Reference setup: what a correct /kairyn:init produces.
make_good() {
  d="$1"; mkdir -p "$d/.kairyn/stages" "$d/.kairyn/templates" "$d/docs/tasks"
  cp "$plugin"/stages/* "$d/.kairyn/stages/"
  cp "$plugin"/templates/* "$d/.kairyn/templates/"
  printf '# Learnings\n\nStages append here.\n' > "$d/.kairyn/learnings.md"
}

make_good "$tmp/good"
check "good layout passes" "bash '$verify' '$tmp/good' '$plugin'"

make_good "$tmp/no-tasks";   rmdir "$tmp/no-tasks/docs/tasks"
expect_fail "missing docs/tasks fails" "bash '$verify' '$tmp/no-tasks' '$plugin'"

make_good "$tmp/no-stage";   rm "$tmp/no-stage/.kairyn/stages/requirements.md"
expect_fail "missing stage file fails" "bash '$verify' '$tmp/no-stage' '$plugin'"

make_good "$tmp/no-tpl";     rm "$tmp/no-tpl/.kairyn/templates/STATE.md"
expect_fail "missing STATE.md template fails" "bash '$verify' '$tmp/no-tpl' '$plugin'"

make_good "$tmp/drift";      echo "x" >> "$tmp/drift/.kairyn/stages/requirements.md"
expect_fail "modified stage copy fails" "bash '$verify' '$tmp/drift' '$plugin'"

make_good "$tmp/no-learn";   rm "$tmp/no-learn/.kairyn/learnings.md"
expect_fail "missing learnings.md fails" "bash '$verify' '$tmp/no-learn' '$plugin'"

make_good "$tmp/bad-learn";  echo "hello" > "$tmp/bad-learn/.kairyn/learnings.md"
expect_fail "wrong learnings heading fails" "bash '$verify' '$tmp/bad-learn' '$plugin'"

make_good "$tmp/stray";      mkdir "$tmp/stray/docs/tasks/2026-01-01-x"
expect_fail "non-empty docs/tasks fails" "bash '$verify' '$tmp/stray' '$plugin'"

mkdir "$tmp/empty"
expect_fail "empty repo fails" "bash '$verify' '$tmp/empty' '$plugin'"

echo
echo "passed: $pass  failed: $failed"
[ "$failed" -eq 0 ]
