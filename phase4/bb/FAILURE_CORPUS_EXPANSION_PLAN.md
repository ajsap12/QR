# BB Failure Corpus Expansion Plan

## Objective

Expand beyond the original hand-selected failures into reproducible randomized and targeted corpora suitable for decoder research.

## Corpus layers

1. **Seed corpus** — existing replayable failures.
2. **Randomized hard-case corpus** — failures discovered from fixed-seed Monte Carlo runs.
3. **Near-miss corpus** — cases where the decoder converges but has unstable trajectories or wrong logical class.
4. **Invariant corpus** — cases unresolved by layered BPGD, restart, and narrow-beam controls.
5. **Cross-code corpus** — equivalent records across multiple BB codes and both sectors.
6. **OOD corpus** — biased, correlated, or mismatched-prior noise.

## Required record fields

- case ID and deterministic seed
- code and sector
- physical error rate and noise model
- packed physical error
- syndrome
- decoder configurations attempted
- syndrome convergence and logical outcome
- residual trajectory
- LLR summary
- decimation and reversal history
- graph component and cycle features
- operation and memory estimates
- split: train, validation, or held-out test

## Scientific boundaries

- Enriched hard-case corpora measure rescue performance, not natural logical-error rates.
- Natural-frequency LER requires separate unfiltered Monte Carlo experiments.
- Hand-selected cases cannot establish generality.
- Held-out cases must remain untouched during RevBPGD trigger tuning.

## Next instrumentation

- residual-change slope
- periodicity/oscillation detector
- near-tie density
- active-component histogram
- short-cycle overlap around selected variables
- first divergence point between decoder variants
- checkpoint and backtracking cost
