# Level 2 Scientific Extraction — arXiv:2408.10001

**Paper:** Coprime Bivariate Bicycle Codes and Their Layouts on Cold Atoms  
**Authors:** Ming Wang; Frank Mueller  
**Status:** machine-extracted draft; not yet human-approved evidence

## Research question
Can a constrained subclass of bivariate bicycle codes provide predictable rate, discover useful short-to-medium codes, and map efficiently to cold-atom hardware?

## Core contributions
- Introduces a coprime-BB subclass using coprimes and the product `xy` in polynomial construction.
- Claims the code rate can be determined before numerical search by specifying a factor polynomial.
- Reports previously unknown short-to-medium-length codes.
- Proposes a cold-atom layout tailored to the construction.
- Reports fewer atom moves and reduced move time for syndrome extraction under the simulated layouts.
- Evaluates an error model including global laser noise.

## Mathematical objects to extract from full text
- Polynomial-ring definition of vanilla and coprime BB codes.
- CSS parity-check matrices and commutation conditions.
- Rate formula and factor-polynomial conditions.
- Distance computation/search procedure.
- Layout embedding and movement-cost objective.

## Algorithms / procedures
- Select factor polynomial and target dimensions.
- Search admissible coprime polynomial pairs.
- Compute code parameters and filter candidates.
- Map checks/data qubits to cold-atom arrays.
- Schedule atom moves and syndrome extraction.
- Simulate logical performance under the stated noise model.

## Assumptions to verify
- Coprimality and ring-size constraints.
- How distance is established: exact, bounded, or heuristic.
- Cold-atom transport, gate, measurement, and global-laser-noise parameters.
- Decoder used in simulations.

## Key claims requiring page-level evidence
- Rate predictability before search.
- Novelty of the reported code instances.
- Quantitative reduction in moves and move time.
- Logical-performance improvement over prior layouts.

## Limitations / risks
- Benefits may be strongest only for short-to-medium codes.
- Layout conclusions are platform-specific.
- Search completeness and distance certification need careful review.
- Hardware noise parameters may not generalize to other cold-atom systems.

## Cross-paper links
- Compare code instances with self-dual BB and erasure-aware BB work.
- Benchmark BPGD/BP-OSD and diffusion decoders on the reported codes.
- Test whether predictable-rate constraints reduce achievable distance or decoder friendliness.

## Page-level review checklist
- Extract every reported `[[n,k,d]]` instance and proof/certification status.
- Record exact baseline layouts and movement metrics.
- Capture all noise parameters and simulation seeds/sample counts if given.
- Separate code-construction novelty from hardware-layout novelty.
