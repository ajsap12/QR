# QEC Research Decision Log

## 2026-07-14 — Frontier-scan conclusion

**Decision:** Do not pursue generic confidence estimation, simple decoder switching, a generic neural decoder, or another undifferentiated BP scheduling variant as the main research claim.

**Reason:** Recent work substantially covers confidence/post-selection, weak/strong routing, adaptive scheduling, neural/GNN decoding and real-time queueing.

**Surviving algorithmic hypothesis:** bounded state restoration for iterative qLDPC decoding, first instantiated as reversible BPGD.

**Surviving infrastructure hypothesis:** decoder runtime/compiler infrastructure with replay, verification, observability and hardware-aware cost models.

---

## 2026-07-14 — RDSM design formalized

Added `docs/RDSM_DESIGN_NOTE.md`.

Key design choices:

- checkpoint complete decoder state;
- trigger restoration only after a defined stall condition;
- bound rollback depth, branch count and total operation budget;
- start with opposite-bit and runner-up alternatives;
- distinguish convergence from logical correctness;
- require matched controls against restart and beam search.

Paper-level working title:

> Bounded State Restoration for Iterative Quantum LDPC Decoding

---

## 2026-07-14 — Gate 1 criteria

Gate 1 uses the existing selected BPGD failure corpus.

Pass criteria:

- solve both invariant failures or at least two additional cases;
- stay within the configured 2x operation budget;
- introduce no regression on cases already solved by sequential BPGD.

Interpretation boundary:

Passing Gate 1 supports broader randomized experiments. It does not establish lower logical error rate.

---

## 2026-07-14 — Prior-art controls fixed

The following controls are mandatory before a novelty or performance claim:

1. sequential BPGD;
2. random-restart or Lottery-style BPGD;
3. depth-limited beam BPGD;
4. BP-OSD or BF-OSD;
5. Relay-BP where a reproducible implementation is available.

The most serious collision risks are narrow beam search, randomized multi-start BP and the parent sequential-BPGD method.

---

## Current evidence status

| Evidence item | Status |
|---|---|
| Frontier literature scan | Complete at decision level; living updates required |
| RDSM theory/design note | Complete |
| Reversible BPGD implementation | Present on research branch |
| GitHub workflow trigger | Configured |
| Gate 1 result | Pending workflow completion |
| Randomized matched-sample LER | Not started |
| Restart control | Not started |
| Narrow-beam control | Not started |
| Relay-BP control | Not started |
| Hardware state/memory model | Not started |

## Logging convention

For every material research decision, record:

- date;
- claim or hypothesis;
- supporting evidence;
- nearest prior art;
- falsification criterion;
- resulting action;
- whether the change affects publication or commercialization strategy.
