from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class StatefulBpgdDiagnostics:
    converged: bool
    decimations: int
    residual_syndrome_weight: int


class StatefulSumProductBpgd:
    """Stateful binary sum-product BP with guided decimation.

    Variable-to-check and check-to-variable messages are initialized once and
    preserved across decimation rounds, matching the paper's "continue BP"
    semantics more closely than repeatedly calling a packaged decoder.
    """

    def __init__(
        self,
        parity_check: Sequence[Sequence[int]],
        error_rate: float,
        *,
        iterations_per_round: int = 100,
        llr_max: float = 25.0,
        numeric_clip: float = 50.0,
    ) -> None:
        if not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be between 0 and 1")
        self.h = np.asarray(parity_check, dtype=np.uint8)
        if self.h.ndim != 2:
            raise ValueError("parity_check must be two-dimensional")
        self.m, self.n = self.h.shape
        self.iterations_per_round = iterations_per_round
        self.llr_max = llr_max
        self.numeric_clip = numeric_clip

        checks, variables = np.nonzero(self.h)
        self.edge_checks = checks.astype(int)
        self.edge_variables = variables.astype(int)
        self.check_edges = [np.flatnonzero(self.edge_checks == c) for c in range(self.m)]
        self.variable_edges = [np.flatnonzero(self.edge_variables == v) for v in range(self.n)]

        initial_llr = math.log((1.0 - error_rate) / error_rate)
        self.channel_llr = np.full(self.n, initial_llr, dtype=float)
        self.variable_to_check = self.channel_llr[self.edge_variables].copy()
        self.check_to_variable = np.zeros(len(self.edge_checks), dtype=float)
        self.last_diagnostics = StatefulBpgdDiagnostics(False, 0, 0)

    def _sum_product_iteration(self, syndrome: np.ndarray) -> None:
        new_check_to_variable = np.empty_like(self.check_to_variable)
        tanh_messages = np.tanh(np.clip(self.variable_to_check / 2.0, -20.0, 20.0))

        for check, edges in enumerate(self.check_edges):
            values = tanh_messages[edges]
            parity_sign = -1.0 if syndrome[check] else 1.0
            for local_index, edge in enumerate(edges):
                if len(edges) == 1:
                    product = parity_sign
                else:
                    mask = np.ones(len(edges), dtype=bool)
                    mask[local_index] = False
                    product = parity_sign * float(np.prod(values[mask]))
                product = min(1.0 - 1e-15, max(-1.0 + 1e-15, product))
                new_check_to_variable[edge] = 2.0 * math.atanh(product)

        self.check_to_variable = np.clip(
            new_check_to_variable,
            -self.numeric_clip,
            self.numeric_clip,
        )

        incoming_sum = np.zeros(self.n, dtype=float)
        np.add.at(incoming_sum, self.edge_variables, self.check_to_variable)
        self.variable_to_check = np.clip(
            self.channel_llr[self.edge_variables]
            + incoming_sum[self.edge_variables]
            - self.check_to_variable,
            -self.numeric_clip,
            self.numeric_clip,
        )

    def posterior_llr(self) -> np.ndarray:
        incoming_sum = np.zeros(self.n, dtype=float)
        np.add.at(incoming_sum, self.edge_variables, self.check_to_variable)
        return self.channel_llr + incoming_sum

    def decode(self, syndrome: Sequence[int]) -> tuple[int, ...]:
        target = np.asarray(syndrome, dtype=np.uint8)
        if target.shape != (self.m,):
            raise ValueError("syndrome length must match parity-check row count")

        frozen = np.zeros(self.n, dtype=bool)
        output = np.zeros(self.n, dtype=np.uint8)

        for round_index in range(self.n):
            for _ in range(self.iterations_per_round):
                self._sum_product_iteration(target)

            posterior = self.posterior_llr()
            output = (posterior < 0.0).astype(np.uint8)
            residual = ((self.h @ output) & 1) ^ target
            residual_weight = int(np.sum(residual))
            if residual_weight == 0:
                self.last_diagnostics = StatefulBpgdDiagnostics(
                    True,
                    round_index,
                    0,
                )
                return tuple(int(bit) for bit in output)

            candidates = np.flatnonzero(~frozen)
            if candidates.size == 0:
                break
            selected = int(candidates[np.argmax(np.abs(posterior[candidates]))])
            hard_bit = int(posterior[selected] < 0.0)
            self.channel_llr[selected] = -self.llr_max if hard_bit else self.llr_max
            frozen[selected] = True

        residual_weight = int(np.sum((((self.h @ output) & 1) ^ target)))
        self.last_diagnostics = StatefulBpgdDiagnostics(
            False,
            self.n,
            residual_weight,
        )
        return tuple(int(bit) for bit in output)
