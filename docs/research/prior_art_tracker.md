# Living Prior-Art Tracker — BP-Family and Search-Assisted QEC Decoders

**Purpose:** establish exactly what each method already does, what it does not do, and whether bounded reversible BPGD is meaningfully distinct.

**Maintenance rule:** add any new paper, repository, patent, or commercial implementation that could invalidate a RevBPGD claim. Update collision risk and differentiation notes immediately.

| Method | Core mechanism | Explicit rollback | Branch/list | Restart/ensemble | Dynamic memory | Dynamic graph/basis | Heavy algebra | Runtime bounded by design | Collision risk | What RevBPGD must prove |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Plain BP / Min-Sum | Iterative Tanner-graph message passing | No | No | No | No | No | No | Yes | 1 | Checkpointed tentative decisions add value beyond ordinary BP. |
| BP-OSD | BP reliability ordering plus ordered-statistics list search | No | Yes | No | No | No | Yes | No | 3 | Repairing the trajectory can reduce reliance on matrix-heavy fallback. |
| BPGD | Greedy reliability-based decimation | No | No | No | No | No | No | Yes | 5 | Bounded undo repairs bad commitments without excessive overhead. |
| Sequential BPGD | Layered scheduling plus greedy decimation | No | No | No | No | No | No | Yes | 5 | Beat the strongest forward-only schedule, not flooding BPGD. |
| Relay-BP | Disordered message memory and relayed BP states | No | Yes | Yes | Yes | No | No | Yes | 4 | State restoration solves cases not handled by altered message dynamics. |
| MBBP-LD | Multiple parity-check bases and candidate selection | No | Yes | Yes | No | Yes | No | Yes | 4 | Retained-prefix rollback is more efficient than parallel basis diversity. |
| Beam Search Decoder | BP-guided top-K hypothesis search | No | Yes | No | No | No | No | Usually capped, not intrinsically | 5 | Better accuracy-cost-memory frontier than matched-width beam search. |
| Lottery BP | Randomized multi-start BP with voting/fallback | No | Yes | Yes | No | No | Sometimes | Usually capped experimentally | 5 | Local repair is more efficient than discarding state and restarting. |
| GARI + ensemble NMS | Graph augmentation/rewiring and ensemble decoding | No | Yes | Yes | No | Yes | No | Yes | 4 | Do not claim graph novelty unless adaptation is online and syndrome-conditioned. |
| Best-First OSD | Likelihood-ordered candidate enumeration | No | Yes | No | No | No | Yes | No | 4 | Similar accuracy with lower state, tail, or hardware cost. |
| RL Sequential BP | Learned forward scheduling/action policy | No | No | No | Policy state | No | No | Yes | 3 | Explicit reversible transitions provide additional benefit and auditability. |
| Memory BP / MBP | Damping, inhibition, or historical message updates | No | No | No | Yes | No | No | Yes | 3 | Full-state restoration differs materially from message memory. |
| Random-Restart BPGD | Independent BPGD attempts with altered seeds/order | No | Yes | Yes | No | No | No | By external cap | 5 | Preserve useful prefixes and solve more at matched total work. |
| Depth-Limited Beam BPGD | Branch at selected decimation decisions | No | Yes | No | No | No | No | Yes | 5 | Demonstrate a distinct checkpoint/state-memory or tail-cost advantage. |

## Working definitions

- **Explicit rollback:** restores a prior decoder state and changes a previous hard commitment.
- **Branch/list:** simultaneously retains or enumerates multiple correction hypotheses.
- **Dynamic memory:** changes message-update dynamics using damping, inhibition, or historical state; this is not equivalent to restoring a checkpoint.
- **Dynamic graph/basis:** changes the Tanner/check representation or runs alternate parity-check bases.
- **Collision risk:** 1 = remote overlap; 3 = partial overlap; 5 = direct mechanistic collision.

## Required source set

- BPGD: https://arxiv.org/abs/2312.10950
- Sequential BPGD: https://arxiv.org/abs/2602.13420
- Relay-BP: https://arxiv.org/abs/2506.01779
- MBBP-LD: https://arxiv.org/abs/2605.14170
- Beam Search Decoder: https://arxiv.org/abs/2512.07057
- Lottery BP: https://arxiv.org/abs/2605.00038
- GARI FPGA work: https://arxiv.org/abs/2510.14060
- Best-First OSD: https://arxiv.org/abs/2605.25777
- RL Sequential BP: https://arxiv.org/abs/2603.10192
- Memory BP: https://arxiv.org/abs/2104.13659
- BP-OSD: https://arxiv.org/abs/2005.07016
