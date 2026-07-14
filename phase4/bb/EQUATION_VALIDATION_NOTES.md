# Equation-Level BP Validation

The immediate diagnostic step is complete.

## Executed checks

Nine hand-calculated tests now validate the current binary LLR implementation:

- channel LLR initialization;
- check-node update for syndrome 0;
- check-node sign inversion for syndrome 1;
- variable-to-check exclusion of the destination edge;
- posterior LLR construction;
- hard-decision sign convention;
- current absolute-LLR reliability convention;
- one-check even-syndrome calculation;
- one-check odd-syndrome calculation.

All nine tests passed.

## Important diagnostic result

A symmetric degree-two check with odd syndrome and equal priors produces exactly zero posterior LLR on both variables after one flooding iteration. This exposes an under-specified behavior with practical impact:

- hard decision at exactly zero;
- selection among equal reliabilities;
- treatment of numerically near-equal reliabilities.

The current implementation maps zero LLR to bit 0 and selects the lowest-index variable when reliabilities tie. Those deterministic choices can redirect every later decimation step.

## Current conclusion

The basic LLR equations and syndrome sign are internally consistent. The next likely sources of the 17 failures are tie semantics, Equation 26 fidelity, update scheduling, and numerical clipping—not a simple check-node sign error.
