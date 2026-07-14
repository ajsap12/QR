# Knowledge Graph Review Queue

The graph is built, but all scientific edges are provisional until their cited evidence objects are checked against the rendered PDFs.

## Priority order

1. `e005-e007` — BPGD, QLDPC target, and BP-OSD comparison
2. `e008-e009` — Coprime BB code family and code-search method
3. `e010-e012` — Diffusion decoder, QLDPC target, and BP-OSD comparison
4. `e013-e015` — Self-dual BB codes and transversal Clifford conditions
5. `e016-e018` — BiBiEQ, erasure noise, and circuit-level assumptions
6. `e003-e004` — Union-find decoder and surface-code target
7. `e001-e002` — Introductory-guide ontology links

## Review checklist for every edge

- Open the rendered PDF, not only extracted text.
- Confirm printed page and PDF page index.
- Confirm equation, figure, table, theorem, or algorithm label.
- Confirm that the edge wording preserves all assumptions and caveats.
- Replace `pending-id-normalization` with exact evidence-object IDs.
- Set `confidence` based on directness of support.
- Promote to `human_reviewed`, or set to `rejected` with a note.

## Promotion gate

No contradiction, research gap, or hypothesis may cite an edge whose `review_status` is `provisional` as established evidence.
