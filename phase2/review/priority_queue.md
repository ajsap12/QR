# Phase 2 Review Queue

## Priority 1

1. `arxiv-1907.11157` — establish shared QEC terminology and baseline taxonomy.
2. `arxiv-2312.10950` — extract claims comparing BPGD, BP-OSD, and BP-SI, including complexity and convergence conditions.
3. `arxiv-2408.10001` — extract BB-code construction/search claims and reported code parameters.
4. `arxiv-2509.22347` — inspect diffusion-decoder comparisons, datasets, noise assumptions, latency claims, and scaling evidence.
5. `arxiv-2602.07578` — inspect erasure schedules, exact/approximation assumptions, pseudo-threshold region, and reported logical-error-rate scaling.

## Extraction checklist for every paper

- bibliographic metadata verified
- code family and code parameters
- decoder and implementation details
- noise model and measurement assumptions
- train/validation/test construction, when applicable
- benchmark baselines and tuning fairness
- primary metrics and uncertainty estimates
- compute environment and reproducibility assets
- central claims with page/section locators
- explicit limitations and author caveats
- candidate contradictions with contextual qualifiers
- reviewer decision and notes

## Initial comparison axes

- BP-OSD vs BPGD under matched QLDPC code and noise assumptions
- BP-OSD vs diffusion decoding under matched BB-code circuit-level noise
- exact correlated-erasure modeling vs independent approximation
- surface-code decoder complexity vs QLDPC decoder complexity
- decoder accuracy/latency tradeoff and worst-case behavior

No comparison should be labeled a contradiction until code family, distance, noise model, metric, training regime, and compute budget have been normalized or recorded as unresolved qualifiers.