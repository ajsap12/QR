# Draft Paper Outline

## Working title

**Reproducible Failure Discovery and Semantic Replay for Quantum LDPC Decoders**

## Core question

Can decoder failures be collected, replayed, classified, and compared in a reproducible way that supports algorithm development beyond aggregate logical-error-rate curves?

## Claimed contribution boundary

The paper should not claim a new best decoder unless Gate 3 and later natural-frequency experiments support it. The core contribution is the research methodology and infrastructure:

- deterministic failure-corpus construction
- semantic replay of decoder trajectories
- matched-sample rescue comparisons
- invariant-failure identification
- separation of hard-case rescue rate from natural-frequency LER
- open artifacts and reproducibility

## Sections

1. Introduction and motivation
2. Related work on decoder benchmarking and failure analysis
3. QR architecture
4. Corpus construction and split policy
5. Semantic replay instrumentation
6. Gate 3 matched-sample experimental design
7. Results across layered BPGD, RevBPGD, restart, and beam controls
8. Failure taxonomy and invariant cases
9. Limitations and natural-frequency boundary
10. Reproducibility and open-source release

## Essential figures

- QR data-flow diagram
- corpus composition by code/rate/sector
- residual trajectories for representative failures
- decoder win-overlap matrix
- logical-success versus operation-cost Pareto plot
- invariant-failure case studies

## Required evidence before submission

- successful Gate 3 run
- held-out test split
- at least two BB code instances
- matched logical-outcome labels
- operation-count and memory comparison
- baseline reproduction checks
- clear no-overclaim statement about enriched corpora

## Possible venues

- Quantum
- npj Quantum Information
- PRX Quantum, only if the empirical insight is strong
- QEC-focused workshop or conference as an earlier release
