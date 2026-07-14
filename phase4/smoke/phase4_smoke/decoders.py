from __future__ import annotations

from itertools import product
from typing import Sequence

from .core import hamming_weight, syndrome, xor_bits


def exhaustive_min_weight_decode(
    h: Sequence[Sequence[int]], target_syndrome: Sequence[int]
) -> tuple[int, ...]:
    """Tiny-instance reference decoder. Exponential; smoke tests only."""
    n = len(h[0]) if h else 0
    target = tuple(int(x) & 1 for x in target_syndrome)
    best: tuple[int, ...] | None = None
    for candidate in product((0, 1), repeat=n):
        if syndrome(h, candidate) == target:
            if best is None or hamming_weight(candidate) < hamming_weight(best):
                best = candidate
    if best is None:
        raise ValueError("No correction matches the requested syndrome")
    return best


def greedy_bit_flip_decode(
    h: Sequence[Sequence[int]],
    target_syndrome: Sequence[int],
    max_steps: int | None = None,
) -> tuple[int, ...]:
    """Deterministic bit-flip baseline for decoder-interface validation."""
    n = len(h[0]) if h else 0
    correction = tuple(0 for _ in range(n))
    target = tuple(int(x) & 1 for x in target_syndrome)
    limit = max_steps if max_steps is not None else max(1, 4 * n)

    for _ in range(limit):
        residual = xor_bits(syndrome(h, correction), target)
        if not any(residual):
            return correction

        scores = [
            sum(row[j] & r for row, r in zip(h, residual))
            for j in range(n)
        ]
        best_j = max(range(n), key=lambda j: (scores[j], -j))
        if scores[best_j] <= 0:
            break
        updated = list(correction)
        updated[best_j] ^= 1
        correction = tuple(updated)

    if syndrome(h, correction) != target:
        raise RuntimeError("Greedy decoder did not converge within the smoke-test limit")
    return correction
