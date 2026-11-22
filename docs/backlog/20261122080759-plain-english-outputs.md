---
title: Stage outputs are not checked for plain English
status: inbox
requester: Jayson
date: 2026-11-22
appetite:
review_by:
---

# Stage outputs are not checked for plain English

**Raw request:** "Based on the playbook in knowledge-base. Let's create a backlog from there." (Jayson, 2026-11-22, Claude Code session) Source playbook: `knowledge-base/03 Playbooks/Agents/01 Using ASD-STE100 with Agents.md`.

**Problem (AI draft, needs a human to confirm):** Stage outputs are read by people and by later stages, but nothing measures whether they are short and have one meaning. Wordy outputs cost tokens and hide conditions. We would know it improved when evals count ASD-STE100 violations per 100 words for each stage output.

**Evidence:**
- Playbook steps 5 and 7: run the checklist on sample outputs and add it to the eval set.
- `.kairyn/stages/` instructions are short, but no eval checks output style.

**Notes:** Inference: a script linter may cover most rules more cheaply than an LLM judge.

# Log

2026-11-22T08:07:59Z [capture] Created from the playbook by Claude. Status inbox, waiting for triage.
