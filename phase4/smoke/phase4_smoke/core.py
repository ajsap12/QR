from __future__ import annotations

from typing import Iterable, Sequence


def syndrome(h: Sequence[Sequence[int]], error: Sequence[int]) -> tuple[int, ...]:
    """Return H e mod 2 for a binary parity-check matrix."""
    if any(len(row) != len(error) for row in h):
        raise ValueError("Parity-check matrix width must match error length")
    return tuple(
        sum((bit & 1) * (e & 1) for bit, e in zip(row, error)) % 2
        for row in h
    )


def xor_bits(a: Sequence[int], b: Sequence[int]) -> tuple[int, ...]:
    if len(a) != len(b):
        raise ValueError("Bit vectors must have the same length")
    return tuple((x ^ y) & 1 for x, y in zip(a, b))


def hamming_weight(bits: Iterable[int]) -> int:
    return sum(int(bit) & 1 for bit in bits)
