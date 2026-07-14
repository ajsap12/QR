# Optimized Stateful BPGD Validation

The pure-Python stateful sum-product engine was accelerated with Numba and then run on the full fixed-seed 12,000-shot corpus.

## Runtime improvement

- Prior pure-Python smoke run: 60 shots in about 26.7 seconds.
- Optimized validation: 12,000 shots in about 79.9 seconds, excluding initial JIT compilation.

This is roughly a 67x improvement in shots per second.

## Validation outcome

The stateful implementation produced 17 pure-BPGD nonconvergences:

- `[[72,12,6]]`: X 0, Z 0
- `[[108,8,10]]`: X 9, Z 7
- `[[144,12,12]]`: X 1, Z 0

Comparison against the original packaged-decoder failure set:

- 11 of the original 16 failures were resolved.
- 5 original failures remained.
- 12 new failures appeared under the custom stateful implementation.

## Conclusion

Persistent BP message state is relevant but is not the only missing element. The next debugging target is exact equation-level fidelity: check-node syndrome sign, posterior reliability definition, update ordering, numerical clipping, and deterministic tie-breaking.

No BP-OSD fallback was used in this validation. Performance benchmarking remains blocked.
