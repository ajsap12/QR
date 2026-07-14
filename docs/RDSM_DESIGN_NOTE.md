# Reversible Decoder State Machine (RDSM)

## Status

**Design note — Gate 1 companion document**

This document defines a bounded, state-aware execution model for iterative quantum decoders. The first implementation target is serial BPGD on BB codes, but the abstraction is intentionally broader than a single decoder.

The design is a research hypothesis, not a performance claim. It must be compared against serial BPGD, bounded beam search, randomized restart methods, BP-OSD, and other search-assisted decoders before any novelty or superiority claim is made.

---

## 1. Problem statement

Belief-propagation decoders with greedy decimation repeatedly:

1. estimate variable reliabilities;
2. choose a variable;
3. freeze or hard-decide it;
4. resume inference.

The decision is normally irreversible. A locally sensible decimation can therefore force later inference into a trapping set, pseudocodeword, or logically incorrect basin. Once this happens, the decoder may continue making internally consistent decisions while losing the path to a valid or logically correct correction.

The QR failure corpus provides a concrete test environment for this hypothesis:

- serial scheduling resolves more selected failures than parallel scheduling;
- tie-breaking and exact-zero-LLR policies appear much less important;
- a small set of invariant failures survives multiple BPGD variants;
- semantic replay exposes residual and decision trajectories suitable for rollback analysis.

The central research question is:

> Can bounded state restoration repair an iterative decoder more efficiently than restarting, branching broadly, or invoking a heavy fallback?

---

## 2. Core hypothesis

A small number of carefully selected rollback operations can escape some BPGD failure basins while preserving most of the common-case speed and memory profile of serial BPGD.

Formally, let an iterative decoder evolve through states

\[
S_0 \rightarrow S_1 \rightarrow \cdots \rightarrow S_t,
\]

where each state contains messages, priors, frozen decisions, the current hard estimate, and the residual syndrome. Standard greedy decoding permits only forward transitions.

RDSM augments the transition system with bounded restoration edges:

\[
S_t \rightarrow S_j' \quad \text{for } j < t,
\]

where `S_j'` is restored from a checkpoint and modified by an alternative local decision or policy.

The number and depth of restoration transitions are bounded by a fixed budget.

---

## 3. Design goals

### G1. Bounded repair

Rollback must have an explicit maximum depth, branch count, and operation budget.

### G2. Common-path preservation

Easy syndromes should follow the same path as serial BPGD with minimal additional overhead.

### G3. Deterministic replay

Given identical inputs, configuration, and seed, the full state trajectory must be reproducible.

### G4. Mechanism isolation

Rollback, alternative-variable branching, check reweighting, graph transformation, and random restart must be evaluated as separate ablations.

### G5. Decoder independence

The state-machine abstraction should eventually support other iterative decoders, although the first implementation is serial BPGD.

### G6. Hardware-aware limits

The design must expose predictable state storage, bounded control flow, and operation counts suitable for later CPU, GPU, FPGA, or hybrid evaluation.

---

## 4. Non-goals

RDSM is not intended to:

- perform unbounded exhaustive search;
- replace exact maximum-likelihood decoding;
- claim universal improvement across all codes and noise models;
- conflate syndrome consistency with logical correctness;
- hide fallback cost behind average latency alone;
- combine every possible enhancement in the first experiment.

---

## 5. Decoder state

A complete RDSM checkpoint should contain enough information to reproduce subsequent inference exactly.

```text
DecoderState
├── round_index
├── channel_llr[n]
├── variable_to_check_messages[E]
├── check_to_variable_messages[E]
├── frozen_mask[n]
├── hard_decision[n]
├── correction_estimate[n]
├── residual_syndrome[m]
├── selected_variables[]
├── decision_records[]
├── residual_trajectory[]
├── message_residual_trajectory[]
├── policy_state
└── deterministic_seed_state
```

The minimum Gate 1 implementation may store full arrays. Later implementations may use deltas or periodic checkpoints to reduce memory.

---

## 6. Decision record

Each irreversible-looking decision must instead be recorded as a reversible transaction.

```text
DecisionRecord
├── decision_index
├── selected_variable
├── selected_bit
├── selected_reliability
├── runner_up_variable
├── runner_up_reliability
├── reliability_margin
├── residual_before
├── residual_after
├── checkpoint_reference
├── alternative_actions[]
└── trigger_features
```

This record supports precise questions such as:

- Which decision first separated success and failure trajectories?
- Did rollback repair a low-margin choice or merely add generic search?
- Which trigger best predicts a useful rollback?
- How much state was required to recover?

---

## 7. State-machine model

```text
INITIALIZE
    ↓
INFER
    ↓
CANDIDATE_DECISION
    ↓
CHECKPOINT
    ↓
COMMIT_TENTATIVE
    ↓
EVALUATE
    ├── solved ───────────────→ ACCEPT
    ├── progressing ──────────→ INFER
    ├── stalled ──────────────→ SELECT_ROLLBACK
    └── budget_exhausted ─────→ FAIL

SELECT_ROLLBACK
    ├── no checkpoint ────────→ FAIL
    └── checkpoint available ─→ RESTORE

RESTORE
    ↓
APPLY_ALTERNATIVE
    ↓
INFER
```

All transitions must emit structured events to the replay log.

---

## 8. Stall and repair triggers

Gate 1 should use simple deterministic triggers. More complex triggers must be added only after baseline results are understood.

Candidate triggers include:

### T1. Residual plateau

The residual syndrome weight has not improved over a fixed window.

\[
\max_{i=t-w+1}^{t} r_i - \min_{i=t-w+1}^{t} r_i < \delta.
\]

### T2. Residual cycle

A recent residual syndrome pattern repeats.

### T3. Message oscillation

A subset of LLR signs or message values alternates with a short period.

### T4. Low decision margin

The reliability difference between the selected and runner-up variable is small.

### T5. Persistent unsatisfied-check cluster

The same local check component remains unsatisfied across multiple rounds.

For Gate 1, T1 and low-margin decision ranking are sufficient. T2–T5 belong in later instrumentation work.

---

## 9. Rollback policies

Rollback policy and alternative action must be separated.

### P1. Last low-margin decision

Restore the most recent checkpoint among decisions with the smallest reliability margin.

### P2. Most causally suspicious decision

Restore the checkpoint whose commit caused the largest residual increase or initiated a plateau.

### P3. Cluster-local decision

Restore the most recent decision touching a persistent unsatisfied-check component.

### P4. Fixed-depth rollback

Restore exactly `d` decisions backward.

Gate 1 currently approximates P1 using a bounded branch stack. Later experiments should compare policies directly.

---

## 10. Alternative actions

After restoration, one of the following actions may be applied:

1. **Opposite-bit decision** for the same variable.
2. **Runner-up variable decision** using the original hard estimate.
3. **Temporary prohibition** of the original variable.
4. **LLR attenuation** for the original decision.
5. **Localized check reweighting.**
6. **Parity-check-basis transformation.**

Only actions 1 and 2 belong in the initial rollback experiment. Actions 4–6 introduce additional mechanisms and require separate ablations.

---

## 11. Reference inference algorithm

```text
function RDSM_Decode(H, syndrome, config):
    state ← initialize_serial_bpgd(H, syndrome)
    checkpoints ← empty bounded store
    operations ← 0

    while operations < config.operation_budget:
        posterior, estimate, residual ← infer(state)
        emit(INFERENCE_EVENT)

        if residual == 0:
            return ACCEPT(estimate, trace)

        candidates ← rank_unfrozen_variables(posterior)
        if candidates is empty:
            return try_rollback_or_fail()

        decision ← construct_decision_record(candidates, state)
        save_checkpoint_if_eligible(state, decision)
        apply_primary_decision(state, decision)
        operations ← operations + decision_cost

        if stall_triggered(state.trace):
            if rollback_budget_exhausted():
                return FAIL(best_candidate, trace)

            checkpoint, alternative ← select_repair(checkpoints)
            state ← restore(checkpoint)
            apply(alternative, state)
            operations ← operations + rollback_cost

    return FAIL(best_candidate, trace)
```

---

## 12. Distinction from nearby methods

### 12.1 Serial BPGD

Serial BPGD changes scheduling but retains irreversible decimation. RDSM adds explicit checkpoint, restore, and alternate-transition semantics.

### 12.2 Random restart or lottery-style BP

A restart discards the current trajectory and starts from a different initialization or random seed. RDSM preserves a useful prefix and repairs a selected local commitment.

The empirical question is whether retained-prefix repair is more efficient than restarting.

### 12.3 Beam search

Beam search retains multiple active hypotheses simultaneously. RDSM normally retains one active path and a bounded checkpoint store, restoring only after a trigger.

A depth-one RDSM can resemble a narrow search. Therefore, novelty cannot rest on the word “rollback.” The research contribution must be demonstrated through:

- trigger-driven restoration;
- retained-prefix execution;
- bounded state and latency;
- a distinct accuracy-cost frontier;
- interpretable causal traces.

### 12.4 BP-OSD

BP-OSD invokes algebraic post-processing after or alongside BP. RDSM attempts to repair the iterative inference trajectory itself and avoids unrestricted Gaussian-elimination/list cost on the common path.

### 12.5 Relay-BP and memory-based BP

Relay-BP modifies message dynamics and ensembles BP legs to escape symmetry. RDSM modifies the execution history by restoring earlier decoder states and applying alternate actions.

### 12.6 List decoding

List decoding retains or generates multiple candidates. RDSM is a bounded execution policy that may produce alternatives, but its defining object is the reversible state trajectory rather than a final candidate list.

---

## 13. Complexity model

Let:

- `E` be Tanner-graph edges;
- `I` be BP iterations per decimation round;
- `D` be ordinary decimation rounds;
- `B` be the maximum rollback count;
- `R_b` be resumed rounds after rollback `b`;
- `C_s` be checkpoint storage cost.

Serial BPGD has approximate time:

\[
T_{\mathrm{BPGD}} = O(E I D).
\]

RDSM has:

\[
T_{\mathrm{RDSM}} = O\left(E I \left(D + \sum_{b=1}^{B} R_b\right)\right).
\]

With a hard total-decimation or operation factor `\alpha`, enforce:

\[
T_{\mathrm{RDSM}} \le \alpha T_{\mathrm{BPGD}}
\]

under the experiment’s operation-count approximation.

Naive full checkpoints require:

\[
M = O(B(E+n+m)).
\]

Possible future reductions include:

- periodic full checkpoints plus deltas;
- copy-on-write message arrays;
- decision-only replay from a prior full checkpoint;
- local-region checkpoints.

---

## 14. Correctness boundaries

A zero residual verifies syndrome consistency:

\[
H\hat e = s.
\]

It does not prove logical correctness. Evaluation must therefore distinguish:

1. convergence / syndrome consistency;
2. correction weight or likelihood;
3. logical success relative to the sampled physical error;
4. decoder runtime and memory.

The selected 17-case failure corpus currently tests convergence behavior. Randomized labeled experiments are required for logical-error claims.

---

## 15. Gate structure

### Gate 1 — Selected failure-corpus repair

Compare:

- serial BPGD;
- RDSM rollback depths 1, 2, and 4.

Pass only if the bounded rollback method:

- resolves both invariant cases or at least two additional cases;
- stays within the configured 2× operation budget;
- introduces no regression on cases already solved by serial BPGD.

Passing Gate 1 justifies broader testing. It does not establish a lower LER.

### Gate 2 — Mechanism comparison

On the same matched samples compare:

- serial BPGD;
- randomized restart BPGD;
- rollback-only RDSM;
- depth-limited beam BPGD;
- BP-OSD where feasible.

Required outputs:

- logical error rate;
- convergence rate;
- mean and tail operation counts;
- state memory;
- uniquely resolved syndrome sets.

### Gate 3 — Randomized generalization

Use at least the `[[72,12,6]]`, `[[108,8,10]]`, and `[[144,12,12]]` BB-code instances across multiple physical error rates and seeds.

### Gate 4 — Hardware-oriented evaluation

Evaluate fixed-point sensitivity, checkpoint memory, branch-control cost, and CPU/GPU/FPGA suitability.

---

## 16. Required ablations

1. Serial BPGD baseline.
2. Checkpoint logging without rollback.
3. Rollback to opposite bit only.
4. Rollback to runner-up variable only.
5. Rollback depth 1, 2, and 4.
6. Random restart with matched operation budget.
7. Narrow beam with matched state budget.
8. Stall-triggered versus fixed-round rollback.
9. Full checkpoint versus reconstructed checkpoint.
10. Optional later: local reweighting and graph transformation as independent mechanisms.

---

## 17. Evidence required for a paper

A credible paper cannot rely only on solving two invariant cases. It should demonstrate at least one of the following:

- lower LER at matched mean and tail cost;
- matched LER at lower computation or memory;
- reproducible elimination of a defined trapping-set class;
- a useful theoretical bound on rollback depth or state requirements;
- a hardware-relevant implementation advantage over narrow beam search.

The strongest result would identify a structural failure class for which bounded restoration has a measurable advantage over both restart and parallel hypothesis retention.

---

## 18. Publication framing

A defensible framing is:

> **Bounded State Restoration for Iterative Quantum LDPC Decoding**

The contribution should be described as:

1. a reversible execution semantics for iterative decoders;
2. a deterministic checkpoint and replay model;
3. trigger-driven bounded restoration policies;
4. matched comparisons against restart and beam alternatives;
5. a failure-corpus methodology for mechanism-level analysis.

Avoid claiming a completely new decoding paradigm until the prior-art audit and experiments establish meaningful distinction.

---

## 19. Relationship to a broader decoder runtime

RDSM can become the first decoder plugin for a larger QR runtime architecture:

```text
QR Runtime
├── Decoder state interface
├── Event and replay log
├── Checkpoint store
├── Policy engine
├── Budget manager
├── Verifier
├── Telemetry
└── Decoder plugins
    ├── Serial BPGD
    ├── RDSM-BPGD
    ├── BP
    └── future iterative decoders
```

The algorithmic work and infrastructure work should remain separable. RDSM must be publishable on decoder behavior even if the broader runtime is not built, while the runtime should support other decoders even if RDSM fails.

---

## 20. Immediate implementation alignment

The current Gate 1 code introduces:

- serial BPGD state snapshots;
- rollback depths 1, 2, and 4;
- opposite-bit and runner-up alternatives;
- a residual-plateau trigger;
- bounded total decimation cost;
- structured result and gate-analysis artifacts.

Next implementation steps after the current run:

1. inspect invariant-case trajectories;
2. validate branch ordering and checkpoint semantics;
3. add explicit event logs for every state transition;
4. implement matched random-restart and narrow-beam controls;
5. add logical-success labels for randomized shots;
6. separate full-state checkpoint cost from operation count.

---

## 21. Go / no-go rule

Continue RDSM research only if bounded restoration provides a reproducible advantage over serial BPGD **and** remains competitive with matched-budget restart or narrow beam search.

Stop or reframe if:

- rollback cannot resolve additional selected failures;
- gains disappear on randomized labeled samples;
- equivalent narrow beam search is simpler or uniformly better;
- checkpoint storage or control cost destroys the intended hardware advantage;
- the exact mechanism is found to be established prior art.

Even a no-go result leaves reusable assets: deterministic replay, checkpoint instrumentation, matched mechanism benchmarks, and a richer failure corpus.
