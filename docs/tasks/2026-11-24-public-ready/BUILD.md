---
task: 2026-11-24-public-ready
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | b10bb6d | 1 | 930698b | 0 |
| T2 | 97258f6 | 1 | 4ed39b4 | 0 |
| T3 | 33469a5 | 2 | 51e3aee | 0 |
| T4 | 134da52 | 1 | 2a069bf | 0 |
