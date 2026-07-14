# Level 2 Scientific Extraction — arXiv:2602.07578

**Paper:** BiBiEQ: Bivariate Bicycle Codes on Erasure Qubits  
**Authors:** Ameya S. Bhave; Navnil Choudhury; Andrew Nemec; Kanad Basu  
**Status:** machine-extracted draft; not yet human-approved evidence

## Research question
How do erasure-aware circuits and schedules change the logical performance and simulation throughput of bivariate bicycle code memories?

## Core contributions
- Introduces BiBiEQ, a compiler from a BB code to an erasure-aware memory circuit.
- Supports user-selected 2EC and 4EC erasure-check schedules.
- Converts erasure circuits into stabilizer circuits for general-purpose decoding.
- Provides BiBiEQ-Exact, preserving joint-erasure correlations, and BiBiEQ-Approx, using an independence approximation for faster sweeps.
- Reports per-round logical error rates and schedule-dependent correctable regions below pseudo-threshold.
- Reports close agreement between exact and approximate engines under 4EC.
- Reports substantially larger LER improvement from distance 6 to 10 than from 10 to 12 under the tested conditions.

## Mathematical objects to extract from full text
- Erasure-channel and mixed fault model.
- Circuit-to-stabilizer conversion map.
- Joint-erasure distribution and independence approximation.
- Per-round LER and pseudo-threshold definitions.
- Accuracy/throughput comparison metrics.

## Algorithms / procedures
- Input a BB code and select an EC schedule.
- Compile erasure checks, resets, and erasure events into `C_E`.
- Convert `C_E` to stabilizer circuit `C` using Exact or Approx engine.
- Decode generated samples and estimate per-round LER.
- Sweep physical parameters and code distances.

## Assumptions to verify
- Physical erasure and Pauli-error mechanisms.
- Decoder and matching/weight treatment after conversion.
- Independence assumptions in BiBiEQ-Approx.
- Sample counts, confidence intervals, and pseudo-threshold estimation.
- BB instances used at distances 6, 10, and 12.

## Key claims requiring page-level evidence
- Exact preservation of joint-erasure correlations.
- Approximation speedup and its quantitative error.
- 4EC agreement between the two engines.
- Reported 10–17x relative difference between the `d=6→10` and `d=10→12` LER gains.
- Boundary of the correctable operating region.

## Limitations / risks
- Approximation quality may depend strongly on schedule and physical parameters.
- Conclusions are below pseudo-threshold and may not extrapolate broadly.
- The tested distance set is limited.
- Compiler fidelity depends on the stated circuit and erasure model.

## Cross-paper links
- Apply the framework to coprime and self-dual BB constructions.
- Compare decoders after exact versus approximate conversion.
- Test diffusion/BPGD under identical erasure-aware data.

## Page-level review checklist
- Extract compiler pseudocode and correlation-preservation argument.
- Record exact circuit components and schedule definitions.
- Capture code instances, parameter grids, samples, seeds, and uncertainty.
- Quantify approximation error separately from decoder error.
