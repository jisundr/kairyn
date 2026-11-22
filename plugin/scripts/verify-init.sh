#!/usr/bin/env bash
# Deterministic check of a repo's kairyn layout.
# Usage: verify-init.sh [--fresh] <repo-dir> [plugin-dir]
#   default  a repo in use: everything kairyn installs is present. Tasks may exist and
#            repo-owned files (.kairyn/stages/) may be edited.
#   --fresh  right after /kairyn:init: also stages match the plugin byte for byte and
#            docs/tasks/ is empty.
# Exit 0 if everything is in place, 1 otherwise (prints each problem), 2 on bad usage.
set -u

usage="usage: verify-init.sh [--fresh] <repo-dir> [plugin-dir]"
fresh=0
case "${1:-}" in
  --fresh) fresh=1; shift ;;
  -*) echo "$usage" >&2; exit 2 ;;
esac
[ $# -ge 1 ] || { echo "$usage" >&2; exit 2; }
repo="$1"
plugin="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
fail=0

problem() { echo "FAIL: $1"; fail=1; }

[ -d "$repo/.kairyn" ]            || problem ".kairyn/ missing"
[ -d "$repo/.kairyn/stages" ]     || problem ".kairyn/stages/ missing"
[ -d "$repo/.kairyn/templates" ]  || problem ".kairyn/templates/ missing"
[ -d "$repo/docs/tasks" ]         || problem "docs/tasks/ missing"

# Every shipped stage and template must be in the repo. Templates are plugin-owned, so they
# must match the plugin. Stages are repo-owned: compared only in --fresh mode.
for kind in stages templates; do
  for src in "$plugin/$kind"/*; do
    [ -e "$src" ] || continue
    name="$(basename "$src")"
    dest="$repo/.kairyn/$kind/$name"
    if [ ! -f "$dest" ]; then
      problem ".kairyn/$kind/$name missing"
    elif { [ "$kind" = templates ] || [ "$fresh" -eq 1 ]; } && ! cmp -s "$src" "$dest"; then
      problem ".kairyn/$kind/$name differs from plugin copy"
    fi
  done
done

# The consumer harness: every shipped file exists (users may edit them, so no byte compare).
while read -r f; do
  f="${f#./}"
  [ -f "$repo/.harness/$f" ] || problem ".harness/$f missing"
done < <(cd "$plugin/harness/.harness" && find . -type f | sort)

# CLAUDE.md carries the kairyn block.
if [ ! -f "$repo/CLAUDE.md" ]; then
  problem "CLAUDE.md missing"
elif ! grep -q '<!-- kairyn:start -->' "$repo/CLAUDE.md" || ! grep -q '<!-- kairyn:end -->' "$repo/CLAUDE.md"; then
  problem "CLAUDE.md is missing the kairyn block (<!-- kairyn:start --> ... <!-- kairyn:end -->)"
fi

# learnings.md: exists and starts with the heading.
learn="$repo/.kairyn/learnings.md"
if [ ! -f "$learn" ]; then
  problem ".kairyn/learnings.md missing"
elif [ "$(head -n 1 "$learn")" != "# Learnings" ]; then
  problem ".kairyn/learnings.md must start with '# Learnings'"
fi

# init must not create tasks or other output.
if [ "$fresh" -eq 1 ] && [ -d "$repo/docs/tasks" ] && [ -n "$(find "$repo/docs/tasks" -mindepth 1 -not -name .gitkeep 2>/dev/null | head -n 1)" ]; then
  problem "docs/tasks/ should be empty after init"
fi

if [ "$fail" -eq 0 ]; then echo "OK: kairyn init layout verified"; fi
exit "$fail"
