#!/usr/bin/env bash
# Dev-only. Regenerate the index tables inside plugin/harness/ (the consumer harness templates)
# from the headers of its docs. Run after editing any doc under plugin/harness/.
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT

bash "$root/plugin/scripts/init.sh" "$t" >/dev/null
python3 "$root/plugin/scripts/harness_docs.py" --root "$t" --write >/dev/null
cp "$t/.harness/README.md" "$root/plugin/harness/.harness/README.md"
python3 - "$t/CLAUDE.md" "$root/plugin/harness/CLAUDE.block.md" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
open(sys.argv[2], "w").write(re.search(r"<!-- kairyn:start -->.*?<!-- kairyn:end -->\n?", text, re.S).group(0))
PY
echo "refreshed plugin/harness index tables"
