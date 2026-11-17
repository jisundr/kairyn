#!/usr/bin/env bash
# Deterministic core of `/kairyn:init`: create .kairyn/ and docs/tasks/ in a repo.
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

echo "CREATED: .kairyn/stages, .kairyn/templates, .kairyn/learnings.md, docs/tasks"
