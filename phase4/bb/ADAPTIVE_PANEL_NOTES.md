# Adaptive Multi-Code, Multi-Sector BP-OSD Panel

Executed on 2026-07-14 using the published BB code instances listed in Table 3 of Bravyi et al. (`arXiv:2308.07915`):

- `[[72,12,6]]`: `l=6`, `m=6`, `A=x^3+y+y^2`, `B=y^3+x+x^2`
- `[[108,8,10]]`: `l=9`, `m=6`, same `A` and `B`
- `[[144,12,12]]`: `l=12`, `m=6`, same `A` and `B`

The implementation independently reconstructs `n` and `k`; published distance values are recorded but not independently certified.

## Execution policy

Each X and Z sector was evaluated separately at `p = 0.02, 0.04, 0.06` under binary code-capacity noise. Sampling proceeded in 100-shot batches until either:

- at least 50 logical failures were observed, or
- 2,000 shots were reached.

This produced 18 data points and 27,000 total shots. All decoded residuals had zero syndrome.

## Interpretation boundary

These results validate multi-code construction, X/Z logical classification, adaptive sampling, and the BP-OSD integration. They are not:

- a threshold estimate;
- a circuit-level simulation;
- a depolarizing-noise result;
- a distance certification;
- a comparison against BPGD, diffusion, or another decoder.

The next scientific gate is a matched second-decoder implementation, beginning with BPGD, followed by same-syndrome paired comparisons against BP-OSD.
