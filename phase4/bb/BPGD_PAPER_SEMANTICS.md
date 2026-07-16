# BPGD Paper Semantics — Verified Against arXiv:2312.10950v2

This note records the exact binary BPGD semantics stated in Algorithm 1 and Section 4.3 of Yao et al., *Belief Propagation Decoding of Quantum LDPC Codes with Guided Decimation*.

## Verified algorithm details

1. **Initialization**
   - Channel LLR for every variable node is initialized as
     `mu_v = log((1-p_x)/p_x)`.
   - Initial variable-to-check messages are initialized from that channel LLR.

2. **BP method and round structure**
   - Each decimation round runs the **sum-product** BP algorithm for exactly `T` iterations.
   - The paper describes proceeding to the next round by **continuing to run BP for another T iterations** after the channel message of the decimated variable is changed.
   - This wording and Algorithm 1 imply message state is retained across rounds rather than rebuilding BP from scratch.

3. **Convergence condition**
   - After each `T`-iteration round, form the hard-decision vector.
   - Return immediately when the hard decision matches the measured syndrome.

4. **Reliability ranking**
   - Select the undecimated variable with maximum reliability `gamma(v)` as defined by Equation (26).
   - The ranking is over undecimated variables only.

5. **Freeze semantics**
   - Freeze by replacing the selected variable's **channel LLR**, not by merely changing a probability in an otherwise fresh decoder.
   - Use `+llrmax` when the current bias is nonnegative and `-llrmax` otherwise.
   - The paper uses `llrmax = 25` in all reported simulations.

6. **Failure handling**
   - Run at most `n` decimation rounds.
   - If all variables are decimated and the hard decision still does not match the syndrome, return `non-convergence`.
   - The paper does not use BP-OSD as a hidden fallback inside BPGD. Any fallback in this repository must therefore be reported separately and excluded from pure-BPGD performance statistics.

## Differences from the repository's first provisional implementation

- The first implementation used minimum-sum BP rather than sum-product.
- It approximated hard freezing using probabilities near 0 or 1 instead of directly controlling a persistent channel LLR of magnitude 25.
- The behavior of `ldpc.BpDecoder.decode()` regarding preservation of internal messages across repeated calls is not documented strongly enough to claim that it implements the paper's "continue BP" semantics.
- The syndrome-safe BP-OSD fallback is an engineering safeguard, not part of Algorithm 1.

## Verification result

A direct test using `ldpc.BpDecoder` with `bp_method="product_sum"`, `T=100`, parallel scheduling, and probability values corresponding to `|LLR|=25` produced pure-BPGD non-convergence counts of:

- `[[72,12,6]]`: X 0/2000, Z 0/2000
- `[[108,8,10]]`: X 11/2000, Z 13/2000
- `[[144,12,12]]`: X 2/2000, Z 0/2000

These results are worse than the earlier minimum-sum provisional implementation and confirm that simply changing the public decoder settings is insufficient. The remaining likely mismatch is persistent message-state handling or a difference between the package's BP implementation and the paper's exact sum-product equations.

## Current gate decision

`blocked_for_faithful_reproduction`

A custom stateful sum-product implementation, or confirmed author code, is required before the repository can claim a faithful BPGD reproduction.
