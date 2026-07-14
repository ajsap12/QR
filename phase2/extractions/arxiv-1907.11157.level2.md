# Level 2 Scientific Extraction — arXiv:1907.11157

**Paper:** Quantum Error Correction: An Introductory Guide  
**Authors:** Joschka Roffe  
**Status:** machine-extracted draft; not yet human-approved evidence

## Scope
Introductory review of quantum error-correction theory and implementation, using simple hand-checkable detection/correction codes and the surface code as the main practical architecture.

## Core contributions
- Explains how code choice affects the full quantum-computing stack.
- Introduces basic quantum coding concepts through simple examples.
- Outlines surface-code construction and operation.
- Discusses practical implementation issues for surface and other QEC codes.

## Mathematical objects to extract from full text
- Stabilizer formalism and syndrome relations.
- Code parameters and distance definitions.
- Logical-operator construction.
- Surface-code parity-check structure.
- Threshold and logical-error scaling relations.

## Algorithms / procedures
- Syndrome measurement and error identification.
- Elementary repetition/detection-code workflows.
- Surface-code correction workflow.

## Assumptions to verify
- Noise model used in examples.
- Whether syndrome extraction is perfect or noisy in each section.
- Boundary conventions for planar/surface-code examples.

## Experimental / implementation focus
This is primarily a review, not a new benchmark paper. Extract implementation constraints, measurement schedules, locality assumptions, and architecture-level trade-offs.

## Limitations
- Introductory rather than exhaustive.
- Some examples intentionally simplified.
- Results should not be treated as new empirical evidence.

## Open questions to capture
- Practical syndrome-extraction bottlenecks.
- Decoder and hardware co-design trade-offs.
- How surface-code assumptions change across device platforms.

## Page-level review checklist
- Record pages for every definition and equation.
- Separate pedagogical examples from general claims.
- Tag review statements versus original results.
- Do not create contradiction records from review prose without checking cited primary sources.
