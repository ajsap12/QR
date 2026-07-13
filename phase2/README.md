# Phase 2 — Reviewed Literature and Knowledge System

This directory turns QEC literature into traceable evidence, structured claims, graph-ready relationships, contradictions, and review queues.

## Scientific rules

1. Every substantive claim must point to a source and location.
2. Machine-extracted claims remain `unreviewed` until a human approves them.
3. Contradictions must record whether differences may be explained by code family, noise model, decoder settings, code distance, or evaluation metric.
4. No hypothesis is treated as a result.
5. No result is called a discovery without independent replication.

## Contents

- `corpus/seed_papers.json` — initial public-literature registry.
- `schemas/evidence.schema.json` — evidence-object contract.
- `schemas/claim.schema.json` — claim and review contract.
- `review/priority_queue.md` — first review sequence and extraction checklist.

## Status

This is the Phase 2 foundation. Metadata entries are source-backed, but full-text evidence extraction and page-level review are still pending.