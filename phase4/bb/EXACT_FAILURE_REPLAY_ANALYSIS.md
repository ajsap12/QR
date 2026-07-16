# Exact BPGD Failure Replay Analysis

The successful GitHub Actions run regenerated the fixed-seed 12,000-shot corpus and replayed the exact 17 stateful BPGD nonconvergence syndromes under controlled iteration-count and clipping variants.

## Failure corpus

- 17 exact cases total
- `[[108,8,10]]` X sector: 9
- `[[108,8,10]]` Z sector: 7
- `[[144,12,12]]` X sector: 1
- No failures from `[[72,12,6]]`

## Exact replay results

| Variant | Resolved | Unresolved |
|---|---:|---:|
| `T=100`, clip 50 baseline | 0 | 17 |
| `T=50`, clip 50 | 9 | 8 |
| `T=200`, clip 50 | 10 | 7 |
| `T=100`, clip 25 | 10 | 7 |
| `T=100`, clip 100 | 0 | 17 |
| `T=200`, clip 25 | 8 | 9 |

## Main findings

1. Increasing clipping from 50 to 100 changes nothing: all 17 cases remain unresolved.
2. Both `T=200, clip=50` and `T=100, clip=25` resolve 10 of 17 cases, the best result among the tested settings.
3. Combining `T=200` with clip 25 is worse than either best single change, resolving only 8 of 17.
4. The response is therefore non-monotonic; more iterations or stronger clipping cannot be assumed to help.
5. Two syndromes remain unresolved under every non-baseline tested variant:
   - `83cc513e8352f861d464fc57dee727be48466bfc45929f6b528cfe5a79fef44a`
   - `d3c5a77227b03f3dd243de72a6f4fd46d4de5c488c521a16e3b9852fc09c879b`

## Decision

Do not replace the baseline with a tuned parameter solely because it resolves more of these cases. The paper reports `T=100` and `llrmax=25`; the internal numerical clip is an implementation detail, not a documented scientific parameter.

The next diagnostic target should be the two invariant cases, followed by the remaining five-to-seven variant-dependent cases. Extend the stateful kernel with:

- exact tie-count instrumentation;
- alternate deterministic and seeded-random tie policies;
- zero-LLR hard-decision policies;
- serial versus flooding update schedules;
- per-round selected-variable and posterior-LLR traces.

Only a setting consistent with the paper or author code should be promoted.
