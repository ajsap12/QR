# QEC Knowledge Graph v0.1

This directory contains the first machine-generated QEC knowledge graph built from the seven Phase 2 seed papers and their structured evidence objects.

## Scientific status

The graph is **provisional**. Nodes and edges derived from evidence files with status `machine_extracted_requires_human_review` remain provisional and must not be treated as established facts.

## Node types

- `paper`
- `code_family`
- `decoder`
- `noise_model`
- `concept`
- `result`
- `evidence_object`

## Edge types

- `studies`
- `uses_decoder`
- `evaluates_under`
- `supports`
- `compares_with`
- `extends`
- `targets`
- `implements`
- `has_evidence`

Every scientific edge must contain:

- `source_paper_id`
- `evidence_file`
- `evidence_ids`
- `review_status`
- `confidence`

## Promotion rule

An edge may be promoted from `provisional` to `reviewed` only when every cited evidence object has been checked against the rendered PDF and marked `human_reviewed`.

## Files

- `qec_kg_v0.1.json` — graph nodes and edges
- `graph.schema.json` — validation schema
- `review_queue.md` — edge-review order and promotion checklist
