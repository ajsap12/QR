# RevBPGD Prior-Art and Differentiation Matrix

## Research claim under test

RevBPGD introduces **triggered, bounded restoration of a prior iterative-decoder state**, followed by an alternate local decision, with the goal of escaping hard BPGD failure basins at lower cost than restart, broad branching, or algebraic fallback.

This is a hypothesis. The word *rollback* alone is not enough to establish novelty.

## Nearest-method comparison

| Comparator | What it already covers | What RevBPGD must prove | Required matched control | Go criterion | No-go criterion |
|---|---|---|---|---|---|
| Sequential BPGD | Strong forward-only scheduling and reduced decimation count | Rollback adds benefit beyond scheduling | Same implementation, syndrome corpus, BP iterations and cost accounting | Additional logical successes with no easy-case regression | Gains disappear against sequential baseline |
| Random restart / Lottery BP | Alternate basins through fresh trajectories | Retained-prefix repair is more efficient than discarding state | Equal total BP iterations and maximum attempts | More unique hard cases at equal/lower mean and p99 work | Restart is equal or better and simpler |
| Depth-limited beam search | Explicit alternative-path exploration | Checkpoint restoration has a state-memory, latency or failure-class advantage | Same candidate decisions and equal branch/checkpoint budget | Better accuracy-cost-memory frontier or clearly distinct structural win | Narrow beam uniformly dominates |
| Relay-BP | Trap escape through memory-modified message dynamics and multiple BP legs | State restoration solves complementary failures or costs less | Same BB codes, noise and operation-accounting model | Complementary unique successes or materially lower implementation burden | Relay-BP dominates accuracy and cost |
| BP-OSD / BF-OSD | Strong list/algebraic fallback | Repair reduces heavy post-processing while retaining accuracy | Same samples and query/operation accounting | Similar LER with lower tail cost or better hardware fit | No meaningful accuracy or cost advantage |
| GARI / MBBP-LD | Graph or parity-basis diversity | Core benefit comes from execution reversal, not hidden graph diversity | Disable graph/basis changes in the core ablation | Rollback-only result survives | Gains require graph/basis changes already covered by prior art |

## Precise differentiators that may survive

1. **Single active path with bounded checkpoint storage**, instead of maintaining a simultaneous beam.
2. **Trigger-driven restoration**, instead of unconditional multi-start or parallel list construction.
3. **Retained-prefix repair**, rather than discarding all prior inference during restart.
4. **Deterministic causal replay**, identifying which decision first drove a successful and failed trajectory apart.
5. **Hard operation and state budgets**, suitable for later hardware analysis.

## Claims that should not be made yet

- First decoder to explore alternatives.
- First backtracking quantum decoder.
- First adaptive BP decoder.
- First stateful or memory-based BP decoder.
- First bounded-search qLDPC decoder.
- First dynamic-graph decoder.

## Minimum publishable evidence

At least one of the following must be shown on matched randomized samples:

- lower logical error rate at matched mean and tail work;
- matched logical error rate at lower work or memory;
- reproducible elimination of a defined trapping-set or failure class;
- a hardware-relevant state/control advantage over narrow beam search;
- a useful theoretical result on restoration depth, trigger validity, or state requirements.

Solving only the hand-selected invariant cases is useful Gate 1 evidence, but is not enough for a paper-level performance claim.

## Immediate collision tests

- Sequential BPGD versus RevBPGD depth 1, 2 and 4.
- Random-restart BPGD versus RevBPGD at equal total BP operations.
- Narrow beam BPGD versus RevBPGD at equal stored-state budget.
- BP-OSD or BF-OSD versus RevBPGD on LER and p99 cost.
- Relay-BP versus RevBPGD on unique failure sets where implementation permits.

## Current status

- RDSM design note: complete.
- Gate 1 implementation: present in the research branch.
- Selected failure-corpus experiment: queued/running through GitHub Actions.
- Randomized LER evidence: not yet available.
- Final novelty conclusion: pending experiments and continuing prior-art review.
