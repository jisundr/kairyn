# 1. Requirements wait for approval in chat

Date: 2026-11-22

## Status
Accepted

## Context
Task 2026-11-22-requirements-gaps closed the playbook gaps in the requirements stage. Before it, a later stage could build from a spec that nobody approved. The approval needed a record that the eval can check. A script or a command could write that record, or the agent could write it.

## Decision
The requirements stage ends with `status: blocked` and `Approval: pending`. After the user approves in chat, the agent writes `Approval: <git user.name>, <timestamp>, "<the user's words>"` and moves the task on. A reply that does not approve changes nothing. No script or command writes the line.

## Consequences
- Every requirements run ends blocked. The eval checks accept `status: blocked` with `Approval: pending`.
- An eval proves that the agent does not write the line from a reply that does not approve.
- Tasks approved before this rule have no approval line, so `exit.py check` refuses them.
