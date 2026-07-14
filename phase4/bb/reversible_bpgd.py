from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd


@dataclass(frozen=True)
class ReversibleConfig:
    semantic: SemanticConfig = SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero")
    max_backtracks: int = 1
    alternatives_per_decision: int = 2
    stall_window: int = 4
    min_residual_improvement: int = 1
    max_total_decimations_factor: float = 2.0


@dataclass(frozen=True)
class ReversibleDiagnostics:
    converged: bool
    residual_syndrome_weight: int
    total_decimations: int
    explored_paths: int
    backtracks_used: int
    rollback_rounds: tuple[int, ...]
    selected_variables: tuple[int, ...]
    residual_trajectory: tuple[int, ...]
    operation_ratio_vs_serial_budget: float


@dataclass
class _State:
    channel_llr: np.ndarray
    v2c: np.ndarray
    c2v: np.ndarray
    frozen: np.ndarray
    previous: np.ndarray
    selected_variables: list[int]
    residual_trajectory: list[int]
    round_index: int

    def clone(self) -> "_State":
        return _State(
            channel_llr=self.channel_llr.copy(),
            v2c=self.v2c.copy(),
            c2v=self.c2v.copy(),
            frozen=self.frozen.copy(),
            previous=self.previous.copy(),
            selected_variables=list(self.selected_variables),
            residual_trajectory=list(self.residual_trajectory),
            round_index=self.round_index,
        )


@dataclass
class _Branch:
    state: _State
    variable: int
    bit: int
    rollback_round: int
    margin: float


class ReversibleBpgd:
    """Bounded rollback extension of serial BPGD.

    The common path is ordinary serial BPGD. At low-margin decisions, snapshots are
    retained. If the path stalls or exhausts its decimation budget, the decoder
    restores a recent snapshot and tries either the opposite hard decision or the
    next-most-reliable variable. This is intentionally bounded and diagnostic; it
    is not an unbounded beam-search implementation.
    """

    def __init__(self, parity_check: Sequence[Sequence[int]], error_rate: float, config: ReversibleConfig) -> None:
        if config.semantic.schedule != "serial":
            raise ValueError("Gate 1 requires a serial BPGD baseline")
        if config.max_backtracks < 0:
            raise ValueError("max_backtracks must be non-negative")
        self.kernel = StatefulSemanticBpgd(parity_check, error_rate, config.semantic)
        self.h = self.kernel.h
        self.m, self.n = self.h.shape
        self.error_rate = error_rate
        self.config = config
        self.last_diagnostics = ReversibleDiagnostics(False, 0, 0, 0, 0, (), (), (), 0.0)

    def _initial_state(self) -> _State:
        initial_llr = math.log((1.0 - self.error_rate) / self.error_rate)
        channel_llr = np.full(self.n, initial_llr, dtype=float)
        return _State(
            channel_llr=channel_llr,
            v2c=channel_llr[self.kernel.edge_variables].copy(),
            c2v=np.zeros(len(self.kernel.edge_checks), dtype=float),
            frozen=np.zeros(self.n, dtype=bool),
            previous=np.zeros(self.n, dtype=np.uint8),
            selected_variables=[],
            residual_trajectory=[],
            round_index=0,
        )

    def _posterior(self, target: np.ndarray, state: _State) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        for _ in range(self.config.semantic.iterations_per_round):
            state.v2c, state.c2v = self.kernel._serial_iteration(
                target, state.channel_llr, state.v2c, state.c2v
            )
        incoming = np.zeros(self.n, dtype=float)
        np.add.at(incoming, self.kernel.edge_variables, state.c2v)
        posterior = state.channel_llr + incoming
        output, _ = self.kernel._hard_decisions(posterior, state.previous)
        residual = ((self.h @ output) & 1) ^ target
        return posterior, output, residual

    def _rank_candidates(self, posterior: np.ndarray, frozen: np.ndarray) -> list[int]:
        candidates = np.flatnonzero(~frozen)
        if candidates.size == 0:
            return []
        reliabilities = np.abs(posterior[candidates])
        order = np.lexsort((candidates, -reliabilities))
        return [int(candidates[index]) for index in order]

    def _apply_decision(self, state: _State, variable: int, bit: int) -> None:
        state.channel_llr[variable] = -self.config.semantic.llr_max if bit else self.config.semantic.llr_max
        state.frozen[variable] = True
        state.selected_variables.append(variable)
        state.round_index += 1

    def _stalled(self, trajectory: list[int]) -> bool:
        window = self.config.stall_window
        if len(trajectory) < window:
            return False
        recent = trajectory[-window:]
        return max(recent) - min(recent) < self.config.min_residual_improvement

    def decode(self, syndrome: Sequence[int]) -> tuple[int, ...]:
        target = np.asarray(syndrome, dtype=np.uint8)
        if target.shape != (self.m,):
            raise ValueError("syndrome length must match parity-check rows")

        serial_budget = self.n
        total_budget = max(serial_budget, int(math.ceil(serial_budget * self.config.max_total_decimations_factor)))
        total_decimations = 0
        explored_paths = 1
        backtracks_used = 0
        rollback_rounds: list[int] = []
        branches: list[_Branch] = []
        state = self._initial_state()
        best_output = state.previous.copy()
        best_residual_weight = int(np.sum(target))
        best_selected: list[int] = []
        best_trajectory: list[int] = []

        while True:
            path_failed = False
            while state.round_index < self.n and total_decimations < total_budget:
                posterior, output, residual = self._posterior(target, state)
                residual_weight = int(np.sum(residual))
                state.residual_trajectory.append(residual_weight)
                if residual_weight < best_residual_weight:
                    best_residual_weight = residual_weight
                    best_output = output.copy()
                    best_selected = list(state.selected_variables)
                    best_trajectory = list(state.residual_trajectory)
                if residual_weight == 0:
                    self.last_diagnostics = ReversibleDiagnostics(
                        True,
                        0,
                        total_decimations,
                        explored_paths,
                        backtracks_used,
                        tuple(rollback_rounds),
                        tuple(state.selected_variables),
                        tuple(state.residual_trajectory),
                        total_decimations / max(1, serial_budget),
                    )
                    return tuple(int(bit) for bit in output)

                ranked = self._rank_candidates(posterior, state.frozen)
                if not ranked:
                    path_failed = True
                    break
                selected = ranked[0]
                selected_bit = int(output[selected])
                selected_rel = float(abs(posterior[selected]))
                second_rel = float(abs(posterior[ranked[1]])) if len(ranked) > 1 else 0.0
                margin = selected_rel - second_rel

                if backtracks_used + len(branches) < self.config.max_backtracks:
                    snapshot = state.clone()
                    branches.append(_Branch(snapshot.clone(), selected, 1 - selected_bit, state.round_index, margin))
                    if len(ranked) > 1 and self.config.alternatives_per_decision > 1:
                        alternate = ranked[1]
                        branches.append(
                            _Branch(snapshot, alternate, int(output[alternate]), state.round_index, margin)
                        )
                    branches.sort(key=lambda item: (item.margin, -item.rollback_round), reverse=True)

                state.previous = output
                self._apply_decision(state, selected, selected_bit)
                total_decimations += 1
                if self._stalled(state.residual_trajectory):
                    path_failed = True
                    break

            if not path_failed and state.round_index >= self.n:
                path_failed = True
            if not path_failed and total_decimations >= total_budget:
                path_failed = True

            if not branches or backtracks_used >= self.config.max_backtracks or total_decimations >= total_budget:
                break

            branch = branches.pop()
            state = branch.state.clone()
            rollback_rounds.append(branch.rollback_round)
            backtracks_used += 1
            explored_paths += 1
            self._apply_decision(state, branch.variable, branch.bit)
            total_decimations += 1

        self.last_diagnostics = ReversibleDiagnostics(
            False,
            best_residual_weight,
            total_decimations,
            explored_paths,
            backtracks_used,
            tuple(rollback_rounds),
            tuple(best_selected),
            tuple(best_trajectory),
            total_decimations / max(1, serial_budget),
        )
        return tuple(int(bit) for bit in best_output)
