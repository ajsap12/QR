# Level 2 Scientific Extraction — arXiv:2306.09767

**Paper:** Union-find quantum decoding without union-find  
**Authors:** Sam J. Griffiths; Dan E. Browne  
**Status:** machine-extracted draft; not yet human-approved evidence

## Research question
Does the union-find decoder actually require the full disjoint-set optimization machinery to retain favorable scaling at practical code sizes?

## Core contributions
- Analyzes cluster behavior in union-find decoding at scale.
- Argues that the disjoint-set data structure is underutilized for analytic and algorithmic reasons.
- Models decoder-generated erasure clusters and reports no percolation threshold in the data structure for any operating mode considered.
- Claims linear-time worst-case complexity at scale for a naive implementation that omits popular optimizations.

## Mathematical objects to extract from full text
- Cluster-growth model.
- Percolation argument and finite-size assumptions.
- Complexity derivation and asymptotic variables.
- Surface-code geometry and syndrome graph definitions.

## Algorithmic workflow
- Initialize defect/erasure clusters.
- Grow clusters until parity conditions are met.
- Produce a correction through a peeling or equivalent recovery stage.
- Compare optimized disjoint-set and simplified implementations.

## Assumptions to verify
- Noise model and syndrome-extraction model.
- Code family, boundary conditions, and lattice geometry.
- Definition of “at scale.”
- Whether complexity includes all decoding stages and memory costs.

## Key claims requiring page-level evidence
- Thresholds are comparable to MWPM.
- Near-linear amortized behavior of the conventional implementation.
- No percolation threshold in the modeled cluster process.
- Linear worst-case complexity for the simplified implementation at scale.

## Limitations / risks
- Complexity claims may depend on decoder mode and graph family.
- Hardware-resource conclusions require architecture-specific validation.
- Asymptotic findings may not imply lower wall-clock time at small sizes.

## Cross-paper links
- Compare accuracy and latency with BP-OSD/BPGD.
- Use as a fast baseline against diffusion or autoregressive neural decoders.
- Check whether conclusions transfer beyond surface-code decoding graphs.

## Page-level review checklist
- Capture theorem/lemma statements and proof dependencies.
- Extract exact benchmark sizes and timing methodology.
- Separate analytic worst-case results from empirical runtime results.
- Record any conditions under which the simplified decoder loses accuracy.
