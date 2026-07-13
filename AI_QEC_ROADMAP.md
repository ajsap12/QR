# AI-QEC Research Lab Roadmap

## Current status

Phase A+ provides a reproducible research-lab scaffold for quantum error correction. It includes literature ingestion, local PDF extraction, citation-aware claim extraction, a knowledge graph, contradiction and hypothesis agents, experiment planning, simulation manifests, dry-run execution, SQLite persistence, and a discovery gate.

## Phase 1 — Repository foundation

- Import the Phase A+ package under `ai_research_lab/`.
- Run unit and end-to-end tests in CI.
- Keep generated databases and large experiment outputs out of Git.
- Require evidence identifiers for machine-generated claims.

**Exit criteria:** clean install, tests passing, documented local run, and versioned seed data.

## Phase 2 — Literature and knowledge system

- Add legally accessible paper PDFs or metadata links.
- Extract page-level evidence chunks.
- Review machine-extracted claims.
- Expand the knowledge graph across code families, noise models, decoders, thresholds, datasets, and assumptions.
- Add deduplication and provenance checks.

**Exit criteria:** reviewed evidence for the priority corpus and traceable knowledge-graph edges.

## Phase 3 — Hypothesis generation

- Rank contradictions by evidence quality and scientific value.
- Generate falsifiable hypotheses.
- Require explicit assumptions, predicted outcomes, failure conditions, and discriminating experiments.
- Add human approval before expensive execution.

**Exit criteria:** a reviewed backlog of testable hypotheses with experiment specifications.

## Phase 4 — Scientific execution

- Implement Stim, BP-OSD, LDPC, and PyTorch benchmark adapters.
- Create reproducible environment locks and dataset manifests.
- Add CPU/GPU execution backends and cost controls.
- Record seeds, versions, metrics, artifacts, and failures.
- Replicate promising results before promotion.

**Exit criteria:** reproducible benchmark runs and independently repeated results.

## Phase 5 — Continuous research loop

- Schedule periodic literature discovery from approved public sources.
- Ingest only new or changed papers.
- Update evidence, claims, graph relationships, contradictions, and experiment priorities.
- Notify reviewers of material changes.
- Never label an output a discovery without completed experiments, replication, and review.

**Exit criteria:** an auditable recurring pipeline with human review and reliable alerts.

## Scientific guardrails

1. Every factual claim must retain provenance.
2. Machine-extracted claims remain untrusted until reviewed.
3. Hypotheses must be falsifiable.
4. Dry-run is the default for execution.
5. Credentials and proprietary PDFs must not be committed.
6. Statistical significance alone is not sufficient; effect size and robustness are required.
7. Discovery candidates require replication and expert review.
