#!/usr/bin/env bash
# Deterministic check that `/kairyn:init` left a repo in the expected state.
# Usage: verify-init.sh <repo-dir> [plugin-dir]
# Exit 0 if everything is in place, 1 otherwise (prints each problem).
set -u

repo="${1:?usage: verify-init.sh <repo-dir> [plugin-dir]}"
plugin="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
fail=0

problem() { echo "FAIL: $1"; fail=1; }

[ -d "$repo/.kairyn" ]            || problem ".kairyn/ missing"
[ -d "$repo/.kairyn/stages" ]     || problem ".kairyn/stages/ missing"
[ -d "$repo/.kairyn/templates" ]  || problem ".kairyn/templates/ missing"
[ -d "$repo/docs/tasks" ]         || problem "docs/tasks/ missing"

# Every shipped stage and template must be copied into the repo.
for kind in stages templates; do
  for src in "$plugin/$kind"/*; do
    [ -e "$src" ] || continue
    name="$(basename "$src")"
    dest="$repo/.kairyn/$kind/$name"
    if [ ! -f "$dest" ]; then
      problem ".kairyn/$kind/$name missing"
    elif ! cmp -s "$src" "$dest"; then
      problem ".kairyn/$kind/$name differs from plugin copy"
    fi
  done
done

# learnings.md: exists and starts with the heading.
learn="$repo/.kairyn/learnings.md"
if [ ! -f "$learn" ]; then
  problem ".kairyn/learnings.md missing"
elif [ "$(head -n 1 "$learn")" != "# Learnings" ]; then
  problem ".kairyn/learnings.md must start with '# Learnings'"
fi

# init must not create tasks or other output.
if [ -d "$repo/docs/tasks" ] && [ -n "$(find "$repo/docs/tasks" -mindepth 1 -not -name .gitkeep 2>/dev/null | head -n 1)" ]; then
  problem "docs/tasks/ should be empty after init"
fi

if [ "$fail" -eq 0 ]; then echo "OK: kairyn init layout verified"; fi
exit "$fail"
