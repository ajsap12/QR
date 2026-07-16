# QR Research Roadmap

## Objective

Determine quickly whether bounded state restoration is a defensible qLDPC decoding contribution while building reusable decoder-engineering infrastructure regardless of the algorithmic result.

## Week 1

### Algorithm

- Complete Gate 1 replay on the selected failure corpus.
- Inspect all newly solved and still-unsolved trajectories.
- Validate checkpoint restoration, branch ordering and operation-budget accounting.
- Emit explicit events for checkpoint, commit, stall, restore, alternative action, solve and fail.

### Prior art

- Maintain `prior_art_tracker.md` as the canonical living record.
- Deep-read the highest-collision methods: sequential BPGD, beam search, Lottery BP and Relay-BP.
- Record exact algorithmic differences rather than relying on labels.

### Decision gate

Proceed only if Gate 1 solves additional cases within budget and causes no regression.

## Month 1

### Gate 2 controls

- Implement matched-budget random-restart BPGD.
- Implement depth-limited beam BPGD using the same candidate ranking.
- Normalize operation counting across baseline, rollback, restart and beam.
- Track peak stored state, mean work and p95/p99 work.

### Failure corpus

- Expand beyond 17 selected cases.
- Generate random failures across multiple physical error rates.
- Separate training/tuning cases from held-out evaluation cases.
- Add logical-success labels using sampled physical errors.

### Instrumentation

Capture:

- residual syndrome trajectory;
- BP message residuals;
- LLR margins;
- first divergence decision;
- rollback depth and reason;
- unique failure signatures;
- checkpoint memory estimate.

## Month 3

### Randomized generalization

Benchmark on:

- `[[72,12,6]]`;
- `[[108,8,10]]`;
- `[[144,12,12]]`;
- multiple physical error rates and random seeds.

Compare:

- sequential BPGD;
- RevBPGD;
- random restart;
- narrow beam;
- BP-OSD or BF-OSD;
- Relay-BP where reproducible.

Primary outputs:

- logical error rate;
- convergence rate;
- mean and p99 operations;
- peak memory/state;
- uniquely resolved syndrome sets;
- accuracy-cost-memory Pareto frontier.

### Paper checkpoint

Draft methods and experimental-design sections only after the matched controls exist.

## Month 6

### Scientific path, if RevBPGD passes

- Identify a structural class of failures where restoration helps.
- Prove or empirically bound useful restoration depth.
- Add hardware-oriented checkpoint compression.
- Evaluate fixed-point sensitivity and branch-control overhead.
- Prepare a preprint and reproducible release.

### Pivot path, if RevBPGD fails

Retain and package:

- deterministic replay;
- failure mining;
- checkpoint/state instrumentation;
- matched mechanism benchmarking;
- decoder plugin interface.

Reframe the research around decoder observability, verification or runtime infrastructure rather than a new decoder claim.

## Month 12

### Research deliverable

One of:

1. a defensible bounded-state-restoration decoder paper; or
2. a decoder failure-analysis/runtime paper demonstrating why restoration does not beat simpler controls.

### Infrastructure deliverable

Prototype QR decoder runtime with:

```text
runtime/
replay/
corpus/
telemetry/
verifier/
plugins/
decoder_ir/
benchmarks/
```

Minimum supported plugins:

- sequential BPGD;
- RevBPGD;
- random-restart BPGD;
- depth-limited beam BPGD.

## Go / No-Go Gates

### Gate 1 — Selected failures

Go if rollback resolves additional cases within 2x work and no regression.

### Gate 2 — Matched alternatives

Go if rollback beats or complements matched-budget restart and narrow beam.

### Gate 3 — Randomized LER

Go if gains persist on held-out randomized labeled samples.

### Gate 4 — Hardware relevance

Go if checkpoint memory and control overhead preserve a meaningful implementation advantage.

## Non-priority areas

Do not divert the main effort into:

- generic confidence estimation;
- simple decoder switching;
- another unqualified BP scheduling tweak;
- a generic GNN, Transformer or diffusion decoder;
- benchmark-only work without a new scientific or engineering insight.
