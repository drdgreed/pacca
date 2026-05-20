---
name: Feature request
about: Propose an addition or behavioral change to PACCA
title: "[FEAT] "
labels: enhancement
assignees: ''
---

## Problem

What workflow, decision quality, or operator experience does the current behavior fall short on? Be concrete — name the agent, the case type, or the dashboard path that motivates the request.

## Proposed change

What you'd like to see, in plain language. If this affects agent reasoning, include a short example of input → desired output.

## Constraint level

If you've read [`docs/HARNESS.md`](../../docs/HARNESS.md), tag the harness-component constraint level your proposal targets:

- [ ] `system_prompt` — agent system prompt copy
- [ ] `tool_description` — YAML tool schema
- [ ] `tool_implementation` — Python tool body
- [ ] `long_term_memory` — institutional-memory `.md` file
- [ ] `middleware` — cross-step hook
- [ ] `orchestrator` — escalation logic outside an agent
- [ ] `eval_suite` — new test cases or judge rubric
- [ ] `not behavioral` — docs, refactor, infra, or build

## Expected impact

If you can express the predicted behavioral delta as a manifest entry (per [`harness/manifests/change_manifest.schema.json`](../../harness/manifests/change_manifest.schema.json)), include the predicted-fixes block here. Otherwise: what failure pattern does this address, and what observation would convince you the change worked?

## Alternatives considered

Briefly. "I considered X but rejected it because Y" is enough — saves a round trip in review.

## Risk

Anything reviewers should weigh: PHI exposure, audit-trail impact, dependency footprint, change to autonomous-decision boundary, breakage of existing eval cases.
