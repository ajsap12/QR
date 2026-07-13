# Level 2 Scientific Extraction — arXiv:2312.10950

**Paper:** Belief Propagation Decoding of Quantum LDPC Codes with Guided Decimation  
**Status:** machine-extracted draft; requires human technical review  
**Source version:** arXiv v2 (2024-06-21)

## 1. Mathematical contributions

### Definitions and formal objects

- **Quantum stabilizer code:** an `[[n,k,d]]` code defined by a commutative stabilizer subgroup of the n-qubit Pauli group.
- **CSS code representation:** separate binary parity-check matrices for X- and Z-type stabilizers, constrained by the CSS commutativity condition.
- **Syndrome decoding:** find an estimated error with the same measured syndrome as the physical error.
- **Degeneracy:** multiple Pauli errors can have the same syndrome and act identically on the logical state because they differ by a stabilizer.
- **BP convergence:** the hard decisions produced by belief propagation satisfy the measured syndrome.
- **Variable reliability:** the magnitude of the BP bias/log-likelihood estimate for a qubit variable.
- **Guided decimation:** sequentially freeze the currently most reliable undecimated variable to its most likely value.

### Core equations and relations

The paper develops the decoder from the standard stabilizer and BP framework. Key equation classes are:

1. Pauli/symplectic representation and commutation relation.
2. Stabilizer matrix and CSS orthogonality constraint.
3. Syndrome as the symplectic product of the error with stabilizer generators.
4. Binary symmetric-channel prior and channel log-likelihood ratio.
5. Variable-to-check and check-to-variable sum-product update equations.
6. Posterior bias/reliability used for the hard decision.
7. Syndrome-match termination condition.
8. Decimation update that replaces the selected variable's channel LLR by a large positive or negative magnitude according to its current bias.

The extraction intentionally does not reproduce equation text where the HTML rendering omitted symbols. Equation identifiers in the source include (1)–(21), with BPGD's decimation update given as Eq. (21).

### Main algorithm

**Binary BPGD over independent Pauli-X errors**

1. Initialize all channel LLRs from the physical error probability.
2. Maintain a set of undecimated variable nodes.
3. Run a fixed number of BP iterations.
4. Form hard decisions from current biases.
5. If the hard decision matches the syndrome, return the estimated error.
6. Otherwise select the undecimated variable with maximum reliability.
7. Freeze it by setting its channel LLR to a large signed magnitude.
8. Repeat until convergence or all variables are decimated.
9. If no syndrome-matching vector is found, report non-convergence.

The paper also extends the idea from binary BP to quaternary BP for depolarizing noise.

### Complexity claims

- Standard BP is treated as a low-complexity, highly parallelizable iterative decoder.
- BP-OSD has higher complexity because its post-processing includes ordered-statistics operations and solving a linear system; the paper cites cubic-style complexity in block length for the compared implementation.
- BP-SI may run BP repeatedly while inactivating stabilizers and also requires a linear-system solve at the end.
- BPGD avoids solving a system of linear equations.
- Worst-case BPGD can perform up to `n` decimation rounds, each containing a fixed number of BP iterations. Therefore, a conservative implementation-level bound is roughly `O(n * T_BP)` for fixed iterations per round, where `T_BP` is the cost of one BP round. For sparse Tanner graphs, this is commonly near linear per BP iteration in the number of graph edges, but the exact bound depends on scheduling and data structures.

## 2. Assumptions

- The primary binary analysis uses CSS codes under independent Pauli-X errors.
- The quaternary extension uses the depolarizing channel.
- Syndrome measurements are assumed perfect.
- Channel error probabilities are known and used to initialize LLRs.
- A fixed maximum number of BP iterations per decimation round is selected.
- A sufficiently large finite LLR magnitude is used in software instead of infinity when freezing a variable.
- Decoder comparisons depend on the particular BP scheduling, normalization, and post-processing parameters used in each benchmark.

## 3. Theorems and proof status

- The paper is primarily algorithmic and empirical rather than theorem-driven.
- It reviews known hardness results for quantum maximum-likelihood decoding variants.
- The main BPGD contribution is supported through algorithm construction, interpretation, and numerical evaluation rather than a general theorem proving optimality or universal convergence.
- No claim of asymptotically optimal decoding is extracted.

## 4. Scientific contribution summary

The central contribution is a QLDPC decoder that uses BP's own soft information to progressively remove ambiguity caused by degeneracy and short-cycle effects. The method aims to retain BP-like simplicity while approaching the performance of stronger BP post-processors. Its main architectural advantage is that it does not require solving linear systems during post-processing.

## 5. Claims requiring review

1. BPGD outperforms BP-OSD order 0 and a specified BP-SI configuration for the tested independent Pauli-X benchmarks.
2. BPGD achieves performance comparable to stronger BP-based post-processors while avoiding linear-system solves.
3. Guided decimation benefits from code degeneracy rather than merely tolerating it.
4. The quaternary variant is competitive with BP-OSD in the high-error-rate depolarizing regime.
5. Complexity comparisons are implementation- and parameter-sensitive and must be checked against the exact equations and benchmark settings.

## 6. Review checklist

- [ ] Verify all mathematical symbols directly against the PDF.
- [ ] Record exact page/equation locations for Eqs. (1)–(21).
- [ ] Extract the precise stated complexity expressions for BP-OSD, BP-SI, and BPGD.
- [ ] Capture Algorithm 1 exactly as structured data.
- [ ] Extract code families, block lengths, physical error rates, iteration counts, and decoder parameters from every experiment.
- [ ] Validate performance claims from figures and tables.
- [ ] Mark each claim approved/rejected/needs-revision.
