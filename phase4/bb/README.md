# Published BB Instance and BP-OSD Adapter

This directory advances the next execution gate with two concrete artifacts:

1. A faithful matrix constructor for the published `[[144,12,12]]` bivariate-bicycle code using `l=12`, `m=6`, `A=x^3+y+y^2`, and `B=y^3+x+x^2`.
2. A thin adapter around the Roffe et al. `ldpc` package's `BpOsdDecoder` API.

## Verified locally

The published instance was constructed and checked with pure Python:

- physical qubits `n = 144`;
- binary ranks `rank(Hx)=66` and `rank(Hz)=66`;
- encoded qubits `k = 144-66-66 = 12`;
- `Hx Hz^T = 0 mod 2`;
- every X and Z stabilizer has weight 6.

This reproduces the published code's matrix dimensions, CSS commutation, stabilizer weight, and encoded dimension. It does **not** independently certify the reported distance `d=12`; distance certification remains a separate computational task.

## BP-OSD adapter

`bposd_adapter.py` delegates decoding to the official `ldpc.BpOsdDecoder` implementation and normalizes its configuration for this lab. It intentionally raises a clear error when the optional package is unavailable rather than silently substituting a toy decoder.

## Next gate

- pin and install a tested `ldpc` release;
- run BP-OSD on syndromes generated from this code under a predeclared code-capacity noise model;
- verify correction syndromes and collect convergence/runtime statistics;
- separately certify or reproduce the distance claim using a documented method.
