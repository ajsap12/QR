from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class OneIterationResult:
    variable_to_check: np.ndarray
    check_to_variable: np.ndarray
    posterior_llr: np.ndarray
    hard_decision: np.ndarray


def channel_llr(error_rate: float) -> float:
    if not 0.0 < error_rate < 1.0:
        raise ValueError("error_rate must be between 0 and 1")
    return math.log((1.0 - error_rate) / error_rate)


def check_message(
    incoming_excluding_target: Sequence[float],
    syndrome_bit: int,
    *,
    clip: float = 1.0 - 1e-15,
) -> float:
    """Binary sum-product check-to-variable update in the LLR domain."""
    product = -1.0 if int(syndrome_bit) & 1 else 1.0
    for message in incoming_excluding_target:
        product *= math.tanh(float(message) / 2.0)
    product = max(-clip, min(clip, product))
    return 2.0 * math.atanh(product)


def variable_message(channel: float, incoming_excluding_target: Sequence[float]) -> float:
    """Variable-to-check update in the LLR domain."""
    return float(channel) + sum(float(value) for value in incoming_excluding_target)


def posterior_llr(channel: float, incoming: Sequence[float]) -> float:
    return float(channel) + sum(float(value) for value in incoming)


def hard_decision(llr: float) -> int:
    """Use the convention e_hat=1 iff posterior LLR is negative."""
    return int(float(llr) < 0.0)


def reliability(llr: float) -> float:
    """Binary BPGD reliability used by the current implementation."""
    return abs(float(llr))


def one_flooding_iteration(
    parity_check: Sequence[Sequence[int]],
    syndrome: Sequence[int],
    error_rate: float,
) -> OneIterationResult:
    h = np.asarray(parity_check, dtype=np.uint8)
    target = np.asarray(syndrome, dtype=np.uint8)
    if h.ndim != 2 or target.shape != (h.shape[0],):
        raise ValueError("invalid parity-check or syndrome dimensions")

    checks, variables = np.nonzero(h)
    edge_count = len(checks)
    initial = channel_llr(error_rate)
    v2c = np.full(edge_count, initial, dtype=float)
    c2v = np.zeros(edge_count, dtype=float)

    for check in range(h.shape[0]):
        edges = np.flatnonzero(checks == check)
        for edge in edges:
            other = [v2c[item] for item in edges if item != edge]
            c2v[edge] = check_message(other, int(target[check]))

    post = np.full(h.shape[1], initial, dtype=float)
    for edge, variable in enumerate(variables):
        post[variable] += c2v[edge]

    return OneIterationResult(
        variable_to_check=v2c,
        check_to_variable=c2v,
        posterior_llr=post,
        hard_decision=(post < 0.0).astype(np.uint8),
    )
