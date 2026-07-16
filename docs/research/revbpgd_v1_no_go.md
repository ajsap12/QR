# RevBPGD v1 — No-Go Decision

**Decision date:** 2026-07-15

## Decision

The current bounded-rollback RevBPGD implementation is closed as a **no-go** research branch.

## Evidence

On the selected 17-case BPGD failure corpus:

- serial BPGD resolved **14/17** cases;
- RevBPGD depth 1 resolved **8/17**;
- RevBPGD depth 2 resolved **8/17**;
- RevBPGD depth 4 resolved **8/17**;
- RevBPGD resolved **0 additional cases**;
- RevBPGD resolved **0/2 invariant cases**;
- four-attempt random restart resolved **15/17**;
- narrow beam width 4 resolved **12/17**.

For the two invariant failures, rollback increased residual syndrome weight:

- `83cc513e...`: residual 3 to 12;
- `bcc41e95...`: residual 5 to 20.

## Interpretation

The tested rule—restore a recent decoder state and apply a local alternative decision after a stall—does not add value over serial BPGD and is dominated by a simpler matched restart control on this corpus.

This result does **not** prove all reversible decoding mechanisms are impossible. It rejects this implementation and its trigger/alternative-selection policy.

## Claims prohibited

Do not claim that RevBPGD v1:

- improves logical error rate;
- repairs invariant BPGD failures;
- beats restart or beam search;
- provides a publishable decoder improvement.

## Preserved value

Keep the implementation as:

- a negative-result baseline;
- a regression test for future mechanisms;
- evidence that selected-corpus gating can kill weak hypotheses early;
- a reference for checkpoint and rollback telemetry.

## Next hypothesis

The next question is:

> Why can randomized trajectories escape at least one deterministic BPGD failure, and can that useful diversity be generated deterministically, cheaply, and reproducibly?

Immediate work:

1. analyze the restart-only success trajectory;
2. structurally diagnose invariant failures;
3. validate faithful BP-OSD, beam, and Relay-BP controls;
4. run held-out and unfiltered randomized experiments only after a new mechanism clears selected-case controls.
