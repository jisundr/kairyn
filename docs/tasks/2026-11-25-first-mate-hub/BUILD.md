---
task: 2026-11-25-first-mate-hub
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | f75b743 | 1 | 687f6ca | 0 |
| T2 | b279515 | 1 | e9d4fb3 | 0 |
| T3 | a9ae614 | 1 | 4dc648b | 0 |
