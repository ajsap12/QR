# Level 2 Scientific Extraction — arXiv:2510.05211

**Paper:** Self-dual bivariate bicycle codes with transversal Clifford gates  
**Authors:** Zijian Liang; Yu-An Chen  
**Status:** machine-extracted draft; not yet human-approved evidence

## Research question
Can bivariate bicycle codes be made self-dual while preserving high encoding rates and supporting transversal Clifford gates?

## Core contributions
- Introduces a broad family of self-dual BB codes.
- Claims transversal CNOT, Hadamard, and S gates.
- Enumerates weight-8 instances up to 200 physical qubits.
- Uses twisted-torus realizations intended to improve distance and locality.
- Reports representative code parameters including `[[16,4,4]]`, `[[40,6,6]]`, `[[56,6,8]]`, `[[64,8,8]]`, `[[120,8,12]]`, `[[152,6,16]]`, and `[[160,8,16]]`.

## Mathematical objects to extract from full text
- Self-duality conditions for CSS/BB constructions.
- Polynomial and lattice representation.
- Logical action of transversal CNOT, H, and S.
- Twisted-torus geometry and stabilizer locality measures.
- Distance calculation or certification method.

## Algorithms / procedures
- Enumerate admissible self-dual weight-8 BB constructions.
- Compute `n`, `k`, and candidate/verified `d`.
- Determine twisted-torus embedding and locality.
- Verify transversal logical-gate action.

## Assumptions to verify
- Exact self-duality convention.
- Conditions under which S is transversal, including possible phase corrections.
- Whether distances are exact or bounded.
- Connectivity model used for locality comparisons.

## Key claims requiring page-level evidence
- Higher rate than compared surface/color-code constructions.
- Valid transversal implementation of the stated Clifford gates.
- Distance/locality benefit of twisted tori.
- Completeness and constraints of the enumeration.

## Limitations / risks
- Enumeration is limited to a stated weight and size range.
- Gate transversality does not alone establish a full fault-tolerant architecture.
- Syndrome-extraction circuits, decoder performance, and circuit-level thresholds require separate validation.

## Cross-paper links
- Compare rate/distance against coprime BB instances.
- Evaluate BPGD/BP-OSD and diffusion decoding on listed self-dual codes.
- Test whether erasure-aware schedules preserve the transversal-gate advantages.

## Page-level review checklist
- Extract proofs for self-duality and each transversal gate.
- Record the exact construction of every representative code.
- Verify distance methodology and locality metrics.
- Distinguish algebraic transversality from circuit-level fault tolerance.
