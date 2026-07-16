from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numba import njit


@dataclass(frozen=True)
class TannerGraph:
    h: np.ndarray
    check_edges: np.ndarray
    check_degrees: np.ndarray
    edge_variables: np.ndarray
    variable_edges: np.ndarray
    variable_degrees: np.ndarray


def build_tanner_graph(parity_check: Sequence[Sequence[int]]) -> TannerGraph:
    h = np.asarray(parity_check, dtype=np.uint8)
    checks, variables = np.nonzero(h)
    edge_variables = variables.astype(np.int64)
    max_check_degree = int(h.sum(axis=1).max())
    max_variable_degree = int(h.sum(axis=0).max())
    check_edges = np.full((h.shape[0], max_check_degree), -1, dtype=np.int64)
    variable_edges = np.full((h.shape[1], max_variable_degree), -1, dtype=np.int64)
    check_degrees = np.zeros(h.shape[0], dtype=np.int64)
    variable_degrees = np.zeros(h.shape[1], dtype=np.int64)
    for edge, (check, variable) in enumerate(zip(checks, variables)):
        check_edges[check, check_degrees[check]] = edge
        check_degrees[check] += 1
        variable_edges[variable, variable_degrees[variable]] = edge
        variable_degrees[variable] += 1
    return TannerGraph(
        h=h,
        check_edges=check_edges,
        check_degrees=check_degrees,
        edge_variables=edge_variables,
        variable_edges=variable_edges,
        variable_degrees=variable_degrees,
    )


@njit(cache=True)
def decode_stateful_sum_product(
    h: np.ndarray,
    check_edges: np.ndarray,
    check_degrees: np.ndarray,
    edge_variables: np.ndarray,
    variable_edges: np.ndarray,
    variable_degrees: np.ndarray,
    syndrome: np.ndarray,
    error_rate: float,
    iterations_per_round: int = 100,
    llr_max: float = 25.0,
    numeric_clip: float = 50.0,
):
    """Numba-accelerated, stateful binary sum-product BPGD decode."""
    m, n = h.shape
    edge_count = edge_variables.shape[0]
    initial_llr = math.log((1.0 - error_rate) / error_rate)
    channel_llr = np.full(n, initial_llr, dtype=np.float64)
    variable_to_check = np.empty(edge_count, dtype=np.float64)
    check_to_variable = np.zeros(edge_count, dtype=np.float64)
    posterior = np.empty(n, dtype=np.float64)
    frozen = np.zeros(n, dtype=np.uint8)
    output = np.zeros(n, dtype=np.uint8)
    for edge in range(edge_count):
        variable_to_check[edge] = channel_llr[edge_variables[edge]]

    for round_index in range(n):
        for _ in range(iterations_per_round):
            for check in range(m):
                degree = check_degrees[check]
                parity_sign = -1.0 if syndrome[check] else 1.0
                for local_edge in range(degree):
                    product = parity_sign
                    for other_local_edge in range(degree):
                        if other_local_edge == local_edge:
                            continue
                        edge = check_edges[check, other_local_edge]
                        value = variable_to_check[edge] / 2.0
                        value = min(20.0, max(-20.0, value))
                        product *= math.tanh(value)
                    product = min(1.0 - 1e-15, max(-1.0 + 1e-15, product))
                    message = 2.0 * math.atanh(product)
                    check_to_variable[check_edges[check, local_edge]] = min(
                        numeric_clip, max(-numeric_clip, message)
                    )

            for variable in range(n):
                incoming = 0.0
                for local_edge in range(variable_degrees[variable]):
                    incoming += check_to_variable[variable_edges[variable, local_edge]]
                posterior[variable] = channel_llr[variable] + incoming
                for local_edge in range(variable_degrees[variable]):
                    edge = variable_edges[variable, local_edge]
                    message = channel_llr[variable] + incoming - check_to_variable[edge]
                    variable_to_check[edge] = min(numeric_clip, max(-numeric_clip, message))

        for variable in range(n):
            output[variable] = 1 if posterior[variable] < 0.0 else 0

        residual_weight = 0
        for check in range(m):
            parity = 0
            for variable in range(n):
                if h[check, variable]:
                    parity ^= output[variable]
            residual_weight += parity ^ syndrome[check]
        if residual_weight == 0:
            return output, True, round_index, 0

        selected = -1
        best_reliability = -1.0
        for variable in range(n):
            if frozen[variable] == 0:
                reliability = abs(posterior[variable])
                if reliability > best_reliability:
                    best_reliability = reliability
                    selected = variable
        if selected < 0:
            break
        channel_llr[selected] = -llr_max if posterior[selected] < 0.0 else llr_max
        frozen[selected] = 1

    residual_weight = 0
    for check in range(m):
        parity = 0
        for variable in range(n):
            if h[check, variable]:
                parity ^= output[variable]
        residual_weight += parity ^ syndrome[check]
    return output, False, n, residual_weight
