# Phase 3A — Falsifiable Hypotheses and Experiment Specifications

Status: design-stage, not executed.

This phase converts the highest-priority Phase 2 research gaps into explicit, falsifiable hypotheses and reproducible experiment plans. No hypothesis is considered supported until its evidence inputs are verified and its experiment is independently replicated.

## Initial scope

1. Matched decoder benchmark: BPGD vs BP-OSD vs diffusion on identical bivariate-bicycle code instances.
2. Reproducibility audit of the seven-paper seed corpus.
3. Structural tradeoff study: self-dual versus unconstrained coprime BB codes.

## Required gates

- evidence links must resolve to reviewed evidence objects;
- assumptions and exclusions must be explicit;
- null and alternative hypotheses must be stated;
- outcome metrics and failure conditions must be measurable;
- random seeds, software versions, code instances, and hardware must be recorded;
- expensive runs require human approval after smoke tests;
- no result may be labeled a discovery before independent replication.
