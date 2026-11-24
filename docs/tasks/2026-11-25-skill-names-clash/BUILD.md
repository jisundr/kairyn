---
task: 2026-11-25-skill-names-clash
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | 9eaf38f | 1 | 24c24de | 0 |
| T2 | df7d733 | 1 | a264489 | 0 |
| T3 | 996dc3d | 2 | beea276 | 0 |
| T4 | 49b613d | 1 | ff20a78 | 0 |
