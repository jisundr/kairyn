#!/usr/bin/env bash
# Deterministic core of `/kairyn:init`: set up kairyn in a repo.
#   .kairyn/   stages, templates, learnings
#   docs/tasks/
#   .harness/  workflow docs and budgets (existing files are kept)
#   CLAUDE.md  created, or a marked kairyn block appended (the rest is never touched)
# Usage: init.sh [repo-dir]   (default: current directory)
# Never overwrites: if .kairyn/ already exists it changes nothing and exits 0.
set -eu

repo="${1:-.}"
plugin="$(cd "$(dirname "$0")/.." && pwd)"

if [ -d "$repo/.kairyn" ]; then
  echo "ALREADY INITIALIZED: .kairyn/ exists, nothing changed"
  ls -A "$repo/.kairyn"
  exit 0
fi

mkdir -p "$repo/.kairyn/stages" "$repo/.kairyn/templates" "$repo/docs/tasks"
cp "$plugin"/stages/* "$repo/.kairyn/stages/"
cp "$plugin"/templates/* "$repo/.kairyn/templates/"
printf '# Learnings\n\nStages append here.\n' > "$repo/.kairyn/learnings.md"

# .harness/: add files that do not exist yet; never overwrite a user's file.
harness="$plugin/harness"
(cd "$harness/.harness" && find . -type f | sort) | while read -r f; do
  f="${f#./}"
  if [ -e "$repo/.harness/$f" ]; then
    echo "KEPT: .harness/$f already exists"
  else
    mkdir -p "$(dirname "$repo/.harness/$f")"
    cp "$harness/.harness/$f" "$repo/.harness/$f"
  fi
done

# CLAUDE.md: create it, or append the kairyn block once. Nothing else is touched.
if [ ! -e "$repo/CLAUDE.md" ]; then
  cp "$harness/CLAUDE.block.md" "$repo/CLAUDE.md"
elif ! grep -q '<!-- kairyn:start -->' "$repo/CLAUDE.md"; then
  printf '\n' >> "$repo/CLAUDE.md"
  cat "$harness/CLAUDE.block.md" >> "$repo/CLAUDE.md"
fi

echo "CREATED: .kairyn/ (stages, templates, learnings), docs/tasks, .harness/, CLAUDE.md block"
