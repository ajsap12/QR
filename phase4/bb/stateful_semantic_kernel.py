from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

TieBreak = Literal["lowest_index", "highest_index", "seeded_random"]
ZeroLlrPolicy = Literal["zero", "one", "previous", "seeded_random"]
Schedule = Literal["parallel", "serial"]


@dataclass(frozen=True)
class SemanticConfig:
    iterations_per_round: int = 100
    llr_max: float = 25.0
    numeric_clip: float = 50.0
    tie_break: TieBreak = "lowest_index"
    zero_llr_policy: ZeroLlrPolicy = "zero"
    schedule: Schedule = "parallel"
    seed: int = 20260714
    tie_tolerance: float = 1e-12


@dataclass(frozen=True)
class SemanticDiagnostics:
    converged: bool
    decimations: int
    residual_syndrome_weight: int
    tie_events: int
    zero_llr_events: int
    selected_variables: tuple[int, ...]


class StatefulSemanticBpgd:
    """Stateful sum-product BPGD with explicit semantic controls.

    This implementation is intended for exact replay of rare failure syndromes,
    not for high-throughput benchmarking. It supports configurable reliability
    tie-breaking, zero-LLR hard decisions, and parallel or serial message updates.
    """

    def __init__(
        self,
        parity_check: Sequence[Sequence[int]],
        error_rate: float,
        config: SemanticConfig,
    ) -> None:
        self.h = np.asarray(parity_check, dtype=np.uint8)
        if self.h.ndim != 2:
            raise ValueError("parity_check must be two-dimensional")
        if not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be between 0 and 1")
        self.error_rate = error_rate
        self.config = config
        self.m, self.n = self.h.shape
        checks, variables = np.nonzero(self.h)
        self.edge_checks = checks.astype(int)
        self.edge_variables = variables.astype(int)
        self.check_edges = [np.flatnonzero(self.edge_checks == c) for c in range(self.m)]
        self.variable_edges = [np.flatnonzero(self.edge_variables == v) for v in range(self.n)]
        self.rng = np.random.default_rng(config.seed)
        self.last_diagnostics = SemanticDiagnostics(False, 0, 0, 0, 0, ())

    def _clip(self, value: float) -> float:
        return min(self.config.numeric_clip, max(-self.config.numeric_clip, value))

    def _hard_decisions(self, posterior: np.ndarray, previous: np.ndarray) -> tuple[np.ndarray, int]:
        output = np.empty(self.n, dtype=np.uint8)
        zero_events = 0
        for index, value in enumerate(posterior):
            if abs(float(value)) <= self.config.tie_tolerance:
                zero_events += 1
                policy = self.config.zero_llr_policy
                if policy == "zero":
                    output[index] = 0
                elif policy == "one":
                    output[index] = 1
                elif policy == "previous":
                    output[index] = previous[index]
                else:
                    output[index] = int(self.rng.integers(0, 2))
            else:
                output[index] = int(value < 0.0)
        return output, zero_events

    def _select_variable(self, posterior: np.ndarray, frozen: np.ndarray) -> tuple[int, bool]:
        candidates = np.flatnonzero(~frozen)
        if candidates.size == 0:
            return -1, False
        reliabilities = np.abs(posterior[candidates])
        maximum = float(np.max(reliabilities))
        tied = candidates[np.abs(reliabilities - maximum) <= self.config.tie_tolerance]
        tie_event = tied.size > 1
        if self.config.tie_break == "lowest_index":
            selected = int(np.min(tied))
        elif self.config.tie_break == "highest_index":
            selected = int(np.max(tied))
        else:
            selected = int(self.rng.choice(tied))
        return selected, tie_event

    def _parallel_iteration(
        self,
        syndrome: np.ndarray,
        channel_llr: np.ndarray,
        v2c: np.ndarray,
        c2v: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        new_c2v = np.empty_like(c2v)
        for check, edges in enumerate(self.check_edges):
            sign = -1.0 if syndrome[check] else 1.0
            values = np.tanh(np.clip(v2c[edges] / 2.0, -20.0, 20.0))
            for local, edge in enumerate(edges):
                product = sign
                for other, value in enumerate(values):
                    if other != local:
                        product *= float(value)
                product = min(1.0 - 1e-15, max(-1.0 + 1e-15, product))
                new_c2v[edge] = self._clip(2.0 * math.atanh(product))
        incoming = np.zeros(self.n, dtype=float)
        np.add.at(incoming, self.edge_variables, new_c2v)
        new_v2c = np.empty_like(v2c)
        for edge, variable in enumerate(self.edge_variables):
            new_v2c[edge] = self._clip(
                channel_llr[variable] + incoming[variable] - new_c2v[edge]
            )
        return new_v2c, new_c2v

    def _serial_iteration(
        self,
        syndrome: np.ndarray,
        channel_llr: np.ndarray,
        v2c: np.ndarray,
        c2v: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        for check, edges in enumerate(self.check_edges):
            sign = -1.0 if syndrome[check] else 1.0
            old_values = np.tanh(np.clip(v2c[edges] / 2.0, -20.0, 20.0))
            for local, edge in enumerate(edges):
                product = sign
                for other, value in enumerate(old_values):
                    if other != local:
                        product *= float(value)
                product = min(1.0 - 1e-15, max(-1.0 + 1e-15, product))
                c2v[edge] = self._clip(2.0 * math.atanh(product))
            touched_variables = np.unique(self.edge_variables[edges])
            for variable in touched_variables:
                variable_edges = self.variable_edges[int(variable)]
                incoming = float(np.sum(c2v[variable_edges]))
                for edge in variable_edges:
                    v2c[edge] = self._clip(channel_llr[variable] + incoming - c2v[edge])
        return v2c, c2v

    def decode(self, syndrome: Sequence[int]) -> tuple[int, ...]:
        target = np.asarray(syndrome, dtype=np.uint8)
        if target.shape != (self.m,):
            raise ValueError("syndrome length must match parity-check rows")
        initial_llr = math.log((1.0 - self.error_rate) / self.error_rate)
        channel_llr = np.full(self.n, initial_llr, dtype=float)
        v2c = channel_llr[self.edge_variables].copy()
        c2v = np.zeros(len(self.edge_checks), dtype=float)
        frozen = np.zeros(self.n, dtype=bool)
        previous = np.zeros(self.n, dtype=np.uint8)
        selected_variables: list[int] = []
        tie_events = 0
        zero_events = 0

        for round_index in range(self.n):
            for _ in range(self.config.iterations_per_round):
                if self.config.schedule == "parallel":
                    v2c, c2v = self._parallel_iteration(target, channel_llr, v2c, c2v)
                else:
                    v2c, c2v = self._serial_iteration(target, channel_llr, v2c, c2v)
            incoming = np.zeros(self.n, dtype=float)
            np.add.at(incoming, self.edge_variables, c2v)
            posterior = channel_llr + incoming
            output, zeros = self._hard_decisions(posterior, previous)
            zero_events += zeros
            residual = ((self.h @ output) & 1) ^ target
            residual_weight = int(np.sum(residual))
            if residual_weight == 0:
                self.last_diagnostics = SemanticDiagnostics(
                    True,
                    round_index,
                    0,
                    tie_events,
                    zero_events,
                    tuple(selected_variables),
                )
                return tuple(int(bit) for bit in output)
            selected, tied = self._select_variable(posterior, frozen)
            if selected < 0:
                break
            tie_events += int(tied)
            selected_variables.append(selected)
            hard_bit = int(output[selected])
            channel_llr[selected] = -self.config.llr_max if hard_bit else self.config.llr_max
            frozen[selected] = True
            previous = output

        residual_weight = int(np.sum((((self.h @ previous) & 1) ^ target)))
        self.last_diagnostics = SemanticDiagnostics(
            False,
            self.n,
            residual_weight,
            tie_events,
            zero_events,
            tuple(selected_variables),
        )
        return tuple(int(bit) for bit in previous)
