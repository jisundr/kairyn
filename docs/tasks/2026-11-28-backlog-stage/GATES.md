---
task: 2026-11-28-backlog-stage
stage: gates
summary: "One row per gate, written by afk.py: the review gates, then .kairyn/afk.yml."
---

# Gates

`design`, `commits` and `sessions` are built in. The exit code decides, then the gate's AI check if `checks:` has one. `not set` means no command: never a pass.

| Gate | Result | Exit | Check |
|---|---|---|---|
| design | fail | 1 | built in |
