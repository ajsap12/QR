from __future__ import annotations

from typing import Sequence

import numpy as np


def gf2_rank(matrix: Sequence[Sequence[int]]) -> int:
    """Return matrix rank over GF(2)."""
    a = np.asarray(matrix, dtype=np.uint8).copy()
    if a.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    rows, cols = a.shape
    rank = 0
    for col in range(cols):
        pivots = np.flatnonzero(a[rank:, col])
        if pivots.size == 0:
            continue
        pivot = rank + int(pivots[0])
        if pivot != rank:
            a[[rank, pivot]] = a[[pivot, rank]]
        for row in np.flatnonzero(a[:, col]):
            if row != rank:
                a[row] ^= a[rank]
        rank += 1
        if rank == rows:
            break
    return rank


def is_in_rowspace(vector: Sequence[int], matrix: Sequence[Sequence[int]]) -> bool:
    """Return True when vector belongs to the GF(2) row space of matrix."""
    a = np.asarray(matrix, dtype=np.uint8)
    v = np.asarray(vector, dtype=np.uint8)
    if a.ndim != 2 or v.ndim != 1 or a.shape[1] != v.shape[0]:
        raise ValueError("vector width must match matrix width")
    return gf2_rank(a) == gf2_rank(np.vstack([a, v]))


def classify_x_residual(
    residual: Sequence[int],
    hx: Sequence[Sequence[int]],
    hz: Sequence[Sequence[int]],
) -> str:
    """Classify an X-error residual for a CSS code.

    Returns:
      - ``syndrome_failure`` when Hz @ residual != 0,
      - ``stabilizer`` when residual is in rowspace(Hx),
      - ``logical_failure`` otherwise.
    """
    r = np.asarray(residual, dtype=np.uint8)
    hz_array = np.asarray(hz, dtype=np.uint8)
    if hz_array.shape[1] != r.shape[0]:
        raise ValueError("residual width must match CSS checks")
    if np.any((hz_array @ r) & 1):
        return "syndrome_failure"
    if is_in_rowspace(r, hx):
        return "stabilizer"
    return "logical_failure"
