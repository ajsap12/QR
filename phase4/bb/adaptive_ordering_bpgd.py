from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from stateful_semantic_kernel import SemanticConfig, SemanticDiagnostics, StatefulSemanticBpgd


@dataclass(frozen=True)
class AdaptiveOrderingConfig:
    semantic: SemanticConfig = SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero")
    candidate_budget: int = 2
    probe_iterations: int = 2
    stall_window: int = 3
    ambiguity_gap: float = 0.25
    max_extra_probe_factor: float = 0.50


class AdaptiveOrderingBpgd(StatefulSemanticBpgd):
    """Serial BPGD with deterministic, bounded one-step candidate reordering.

    The decoder follows ordinary serial BPGD unless the residual stalls or the
    top reliability gap is small. At a trigger, it probes a bounded number of
    top-ranked variables and selects the candidate producing the best immediate
    residual trajectory. This is deliberately narrower than beam search: only
    one live state is retained.
    """

    def __init__(self, parity_check: Sequence[Sequence[int]], error_rate: float, config: AdaptiveOrderingConfig):
        super().__init__(parity_check, error_rate, config.semantic)
        self.adaptive_config = config
        self.last_adaptive = {}

    def _rank(self, posterior: np.ndarray, frozen: np.ndarray) -> list[int]:
        candidates = np.flatnonzero(~frozen)
        if candidates.size == 0:
            return []
        return [int(v) for v in candidates[np.argsort(-np.abs(posterior[candidates]), kind="stable")]]

    def _probe_score(
        self,
        target: np.ndarray,
        channel_llr: np.ndarray,
        v2c: np.ndarray,
        c2v: np.ndarray,
        previous: np.ndarray,
        variable: int,
        bit: int,
    ) -> tuple[int, float]:
        probe_channel = channel_llr.copy()
        probe_v2c = v2c.copy()
        probe_c2v = c2v.copy()
        probe_channel[variable] = -self.config.llr_max if bit else self.config.llr_max
        output = previous.copy()
        posterior = probe_channel.copy()
        for _ in range(self.adaptive_config.probe_iterations):
            probe_v2c, probe_c2v = self._serial_iteration(target, probe_channel, probe_v2c, probe_c2v)
        incoming = np.zeros(self.n, dtype=float)
        np.add.at(incoming, self.edge_variables, probe_c2v)
        posterior = probe_channel + incoming
        output, _ = self._hard_decisions(posterior, previous)
        residual = ((self.h @ output) & 1) ^ target
        return int(np.sum(residual)), float(abs(posterior[variable]))

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
        residual_history: list[int] = []
        reorder_events: list[dict] = []
        probe_count = 0
        max_probes = max(1, int(math.ceil(self.n * self.adaptive_config.max_extra_probe_factor)))

        for round_index in range(self.n):
            for _ in range(self.config.iterations_per_round):
                v2c, c2v = self._serial_iteration(target, channel_llr, v2c, c2v)
            incoming = np.zeros(self.n, dtype=float)
            np.add.at(incoming, self.edge_variables, c2v)
            posterior = channel_llr + incoming
            output, zeros = self._hard_decisions(posterior, previous)
            residual = ((self.h @ output) & 1) ^ target
            residual_weight = int(np.sum(residual))
            residual_history.append(residual_weight)

            if residual_weight == 0:
                self.last_diagnostics = SemanticDiagnostics(True, round_index, 0, 0, int(zeros), tuple(selected_variables))
                self.last_adaptive = {"reorder_events": reorder_events, "probe_count": probe_count, "residual_history": residual_history}
                return tuple(int(bit) for bit in output)

            ranked = self._rank(posterior, frozen)
            if not ranked:
                break
            baseline = ranked[0]
            gap = float(abs(posterior[ranked[0]]) - abs(posterior[ranked[1]])) if len(ranked) > 1 else float("inf")
            stalled = len(residual_history) >= self.adaptive_config.stall_window and min(residual_history[-self.adaptive_config.stall_window:]) >= residual_history[-self.adaptive_config.stall_window]
            ambiguous = gap <= self.adaptive_config.ambiguity_gap
            chosen = baseline

            if (stalled or ambiguous) and probe_count < max_probes and len(ranked) > 1:
                choices = ranked[: max(1, self.adaptive_config.candidate_budget)]
                scored = []
                for variable in choices:
                    bit = int(output[variable])
                    score = self._probe_score(target, channel_llr, v2c, c2v, previous, variable, bit)
                    scored.append((score[0], -score[1], variable, bit))
                    probe_count += 1
                    if probe_count >= max_probes:
                        break
                scored.sort()
                chosen = int(scored[0][2])
                if chosen != baseline:
                    reorder_events.append({
                        "round": round_index,
                        "reason": "stall" if stalled else "ambiguity",
                        "baseline_variable": int(baseline),
                        "chosen_variable": chosen,
                        "reliability_gap": gap,
                        "probe_scores": [list(item) for item in scored],
                    })

            hard_bit = int(output[chosen])
            channel_llr[chosen] = -self.config.llr_max if hard_bit else self.config.llr_max
            frozen[chosen] = True
            selected_variables.append(chosen)
            previous = output.copy()

        residual_weight = int(np.sum((((self.h @ previous) & 1) ^ target)))
        self.last_diagnostics = SemanticDiagnostics(False, self.n, residual_weight, 0, 0, tuple(selected_variables))
        self.last_adaptive = {"reorder_events": reorder_events, "probe_count": probe_count, "residual_history": residual_history}
        return tuple(int(bit) for bit in previous)
