---
name: model-routing
order: 50
optional: true
purpose: Plan the next routing stage for an LLM feature that sends every request to one model.
---

# Stage: model-routing

Optional: run it after `requirements` to cut model cost or latency.

| Stage | Adds | When |
|---|---|---|
| 0 | Logs: model, tokens, cost, latency, quality per request | first |
| 1 | Failover: circuit breaker, backup provider | always |
| 2 | Semantic cache | requests repeat |
| 3 | Rules: length, keywords, type | clear easy and hard classes |
| 4 | Semantic routing | rules miss paraphrases |
| 5 | Cascade: cheap model, escalate on failed check | difficulty hidden |
| 6 | Trained router | labeled traffic, 3-5 leave savings |
| 7 | Cascade routing | three or more models |

## Inputs
- The task's `STATE.md` and `REQUIREMENTS.md`.

## Steps
1. Get timestamps from `date` (see `_template.md`, Time).
2. Find every LLM call: file, model, purpose.
3. Plan only the lowest missing stage.
4. Plan it: a flag, rules and thresholds in config, a log of route and reason per request, shadow mode first.
5. Humans set the quality bar (eval set, scorer, minimum per class), goals and thresholds. Use only values the user or requirements give. Record the others as open decisions.

## Output
`MODEL-ROUTING.md`, front matter `stage: model-routing` (see `_template.md`, Output), then:
- `## Call sites`: table
- `## Next stage`: first line `Stage <n>: <name>`, then why
- `## Decisions`: `D1`, `D2`: value and source, or `open`
- `## Build plan`
- `## Gates`: quality bar per class, shadow savings, router p95, failover tested, human review

Write it in ASD-STE100 (see `_template.md`, Writing).

## Exit criteria
- [ ] One next stage, grounded in the code. No invented numbers.

## State update
As in `_template.md`. Add `model-routing` to `stages`. Open decisions: set it `in-progress`, `stage: model-routing`, `status: blocked`, log them. Else set it `done`, `status: done`.

## Learnings
Append to `.kairyn/learnings.md`.
