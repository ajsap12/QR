# Phase 2E Cross-Paper Comparison Matrix

Status: provisional; based on machine-extracted evidence objects pending independent locator verification.

| Paper | Primary code family | Decoder / method | Noise model emphasis | Main contribution | Key comparison basis | Principal limitation for synthesis |
|---|---|---|---|---|---|---|
| Quantum Error Correction: An Introductory Guide | Surface-code and general stabilizer foundations | Educational overview | General phenomenological and implementation-oriented discussion | Defines common QEC concepts and terminology | Serves as ontology/foundational reference | Not a benchmark paper; results are pedagogical rather than directly comparable |
| Belief Propagation Decoding of Quantum LDPC Codes with Guided Decimation | Quantum LDPC | BPGD; compared with BP-OSD/BP-SI | Paper-specific simulated QLDPC settings | Adds guided decimation to BP and seeks to avoid linear-system solves | Decoder accuracy, convergence behavior, and complexity | Comparability depends on exact code ensemble, BP schedule, and simulation budget |
| Union-find quantum decoding without union-find | Surface code | Union-find-inspired decoder | Surface-code syndrome decoding | Reformulates cluster-growth decoding without explicit union-find data structures | Runtime/implementation behavior and decoding performance | Different code family and noise assumptions from BB/QLDPC papers |
| Coprime Bivariate Bicycle Codes | Bivariate bicycle / QLDPC | Code construction and search, not primarily a decoder | Code-construction evaluation; decoder/noise details must be matched per experiment | Algebraic construction/search for coprime BB codes | Code parameters, distance, rate, and layout properties | Cannot be directly ranked against decoder papers without fixing a common decoder and noise model |
| Decoding quantum LDPC codes with diffusion | Quantum LDPC / BB examples | Diffusion-based neural decoder; compared with BP-OSD | Simulated QLDPC/BB decoding regimes | Applies diffusion modeling to QLDPC decoding | Logical error rate, latency, scaling, and baseline comparison | Training distribution, architecture, hardware, and inference budget may dominate comparisons |
| Self-dual bivariate bicycle codes with transversal Clifford gates | Self-dual BB / CSS | Code construction and logical-gate analysis | Fault-tolerance and code-property emphasis | Connects self-dual BB structure to transversal Clifford gates | Code parameters and gate implementability | Not a decoder-performance study; requires separate fault-tolerant overhead analysis |
| BiBiEQ: Bivariate Bicycle Codes on Erasure Qubits | Bivariate bicycle | Erasure-aware decoding/evaluation | Erasure and circuit-level noise | Studies BB behavior in erasure-dominated hardware regimes | Logical error rate under erasure/circuit-level conditions | Specialized noise regime; results should not be generalized to depolarizing noise |

## Pairwise synthesis priorities

1. **BPGD vs diffusion decoder** — strongest direct decoder comparison candidate, but only after matching code instances, noise model, stopping rules, and compute budget.
2. **Coprime BB vs self-dual BB vs BiBiEQ** — code-family synthesis across construction, logical gates, and erasure hardware assumptions.
3. **Union-find vs QLDPC decoders** — useful primarily as an architectural contrast between topological/local cluster decoding and sparse-graph inference.
4. **Foundational guide vs all papers** — terminology and ontology alignment, not performance comparison.

## Comparison rule

No statement of superiority is accepted unless all of the following are matched or explicitly normalized:

- code family and exact code parameters;
- physical noise model and syndrome-measurement assumptions;
- decoder stopping criteria and failure definition;
- compute platform, wall-clock budget, and parallelism;
- number of Monte Carlo samples and confidence intervals;
- preprocessing, training data, and hyperparameter-search budget.
