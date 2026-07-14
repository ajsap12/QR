# Phase 4A CPU Smoke Tests

These tests validate only the shared decoder interface and binary syndrome conventions on a tiny repetition-code example. They are **not** implementations of BP-OSD, BPGD, or diffusion decoding and must not be used for scientific performance claims.

## Run

From this directory:

```bash
python -m unittest test_smoke -v
```

## Executed result

Local execution on 2026-07-13:

- 4 tests run
- 4 passed
- runtime below 1 second
- CPU only
- Python standard library only

Validated:

- binary syndrome calculation;
- dimension checking;
- exhaustive minimum-weight reference decoding on all single-bit errors of the 3-bit repetition code;
- deterministic bit-flip adapter returning a syndrome-matching correction.

## Gate status

`approved_smoke_test` for the generic interface only.

Still blocked before the scientific pilot:

- faithful BP-OSD adapter;
- faithful BPGD adapter;
- diffusion model implementation/checkpoint;
- published BB-code instance registry;
- matched noise and syndrome conventions;
- verified Phase 2 evidence locators.
