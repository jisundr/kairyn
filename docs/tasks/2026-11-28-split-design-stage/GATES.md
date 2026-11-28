---
task: 2026-11-28-split-design-stage
stage: gates
summary: "One row per gate, written by afk.py: the review gates, then .kairyn/afk.yml."
---

# Gates

`design`, `commits` and `sessions` are built in. The exit code decides, then the gate's AI check if `checks:` has one. `not set` means no command: never a pass.

| Gate | Result | Exit | Check |
|---|---|---|---|
| design | pass | 0 | built in |
| commits | pass | 0 | built in |
| sessions | pass | 0 | built in |
| evals | pass | 0 | built in |
| testing | pass | 0 | - |
| contract | pass | 0 | - |
| accessibility | not set | - | - |
| performance | not set | - | - |
| observability | not set | - | - |
| security | not set | - | - |
