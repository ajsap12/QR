from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

Matrix = list[list[int]]
Monomial = tuple[int, int]


def _shift_matrix(l: int, m: int, dx: int, dy: int) -> Matrix:
    size = l * m
    out = [[0] * size for _ in range(size)]
    for x in range(l):
        for y in range(m):
            src = x * m + y
            dst = ((x + dx) % l) * m + ((y + dy) % m)
            out[src][dst] = 1
    return out


def _xor_matrices(matrices: Sequence[Matrix]) -> Matrix:
    if not matrices:
        raise ValueError("At least one monomial is required")
    return [
        [sum(values) & 1 for values in zip(*rows)]
        for rows in zip(*matrices)
    ]


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)]


def _hstack(left: Matrix, right: Matrix) -> Matrix:
    return [a + b for a, b in zip(left, right)]


def gf2_rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    width = len(matrix[0])
    rows = [sum((bit & 1) << j for j, bit in enumerate(row)) for row in matrix]
    rank = 0
    for column in range(width):
        pivot = next((i for i in range(rank, len(rows)) if (rows[i] >> column) & 1), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and ((rows[i] >> column) & 1):
                rows[i] ^= rows[rank]
        rank += 1
    return rank


def css_commutes(hx: Matrix, hz: Matrix) -> bool:
    for xrow in hx:
        for zrow in hz:
            if sum(a * b for a, b in zip(xrow, zrow)) & 1:
                return False
    return True


@dataclass(frozen=True)
class BBCode:
    l: int
    m: int
    a_terms: tuple[Monomial, ...]
    b_terms: tuple[Monomial, ...]
    hx: Matrix
    hz: Matrix

    @property
    def n(self) -> int:
        return 2 * self.l * self.m

    @property
    def k(self) -> int:
        return self.n - gf2_rank(self.hx) - gf2_rank(self.hz)

    @property
    def x_check_weights(self) -> tuple[int, ...]:
        return tuple(sum(row) for row in self.hx)

    @property
    def z_check_weights(self) -> tuple[int, ...]:
        return tuple(sum(row) for row in self.hz)


def build_bb_code(
    l: int,
    m: int,
    a_terms: Iterable[Monomial],
    b_terms: Iterable[Monomial],
) -> BBCode:
    a_tuple = tuple(a_terms)
    b_tuple = tuple(b_terms)
    a = _xor_matrices([_shift_matrix(l, m, dx, dy) for dx, dy in a_tuple])
    b = _xor_matrices([_shift_matrix(l, m, dx, dy) for dx, dy in b_tuple])
    hx = _hstack(a, b)
    hz = _hstack(_transpose(b), _transpose(a))
    if not css_commutes(hx, hz):
        raise ValueError("Constructed CSS checks do not commute")
    return BBCode(l=l, m=m, a_terms=a_tuple, b_terms=b_tuple, hx=hx, hz=hz)


def published_72_12_instance() -> BBCode:
    """Bravyi et al. [[72,12,6]] BB instance; distance not re-certified here."""
    return build_bb_code(
        6,
        6,
        a_terms=((3, 0), (0, 1), (0, 2)),
        b_terms=((0, 3), (1, 0), (2, 0)),
    )


def published_108_8_instance() -> BBCode:
    """Bravyi et al. [[108,8,10]] BB instance; distance not re-certified here."""
    return build_bb_code(
        9,
        6,
        a_terms=((3, 0), (0, 1), (0, 2)),
        b_terms=((0, 3), (1, 0), (2, 0)),
    )


def published_144_12_instance() -> BBCode:
    """Bravyi et al. [[144,12,12]] BB instance; distance not re-certified here."""
    return build_bb_code(
        12,
        6,
        a_terms=((3, 0), (0, 1), (0, 2)),
        b_terms=((0, 3), (1, 0), (2, 0)),
    )


def published_primary_panel() -> tuple[tuple[str, BBCode], ...]:
    """Small published panel used for bounded CPU integration sweeps."""
    return (
        ("[[72,12,6]]", published_72_12_instance()),
        ("[[108,8,10]]", published_108_8_instance()),
        ("[[144,12,12]]", published_144_12_instance()),
    )
