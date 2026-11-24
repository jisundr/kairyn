---
task: 2026-11-24-multi-repo
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | d1a8a82 | 1 | a87f569 | 0 |
| T2 | 3e14774 | 1 | b48f86f | 0 |
| T3 | 3e5027b | 1 | 1c08408 | 0 |
