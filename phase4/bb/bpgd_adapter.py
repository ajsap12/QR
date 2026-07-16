from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class BpgdConfig:
    error_rate: float
    max_iter: int = 100
    bp_method: str = "ms"
    ms_scaling_factor: float = 0.0
    decimation_limit: int | None = None
    freeze_epsilon: float = 1e-9
    syndrome_safe_fallback: bool = True
    fallback_osd_order: int = 7


@dataclass(frozen=True)
class BpgdDiagnostics:
    converged_without_fallback: bool
    fallback_used: bool
    syndrome_valid: bool
    decimations: int
    frozen_one_count: int
    frozen_zero_count: int
    final_residual_syndrome_weight: int


class BpgdAdapter:
    """Binary BP-guided-decimation research implementation.

    BP is rerun after freezing the most reliable undecimated variable to its
    current hard decision. If guided decimation does not produce a valid
    syndrome match, an explicit BP-OSD fallback may be used. Fallback use is
    exposed in diagnostics and must be excluded or separately reported in any
    BPGD performance claim.

    This is an independent implementation and remains provisional until checked
    line-by-line against the final paper version or official author code.
    """

    def __init__(self, parity_check: Sequence[Sequence[int]], config: BpgdConfig):
        if not 0.0 < config.error_rate < 1.0:
            raise ValueError("error_rate must be between 0 and 1")
        if not 0.0 < config.freeze_epsilon < 0.5:
            raise ValueError("freeze_epsilon must be between 0 and 0.5")
        try:
            from ldpc import BpDecoder, BpOsdDecoder  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the pinned `ldpc` package before using BpgdAdapter") from exc

        self._bp_decoder_type = BpDecoder
        self._bposd_decoder_type = BpOsdDecoder
        self._parity_check = np.asarray(parity_check, dtype=np.uint8)
        self._config = config
        self.last_diagnostics = BpgdDiagnostics(False, False, False, 0, 0, 0, 0)

    @property
    def last_decimations(self) -> int:
        return self.last_diagnostics.decimations

    def _is_valid(self, output: np.ndarray, target: np.ndarray) -> bool:
        return bool(np.array_equal((self._parity_check @ output) & 1, target))

    def decode(self, syndrome: Sequence[int]) -> tuple[int, ...]:
        target = np.asarray(syndrome, dtype=np.uint8)
        n = self._parity_check.shape[1]
        probabilities = np.full(n, self._config.error_rate, dtype=float)
        frozen = np.zeros(n, dtype=bool)
        frozen_values = np.zeros(n, dtype=np.uint8)
        limit = self._config.decimation_limit or n

        decoder = self._bp_decoder_type(
            self._parity_check,
            error_rate=self._config.error_rate,
            max_iter=self._config.max_iter,
            bp_method=self._config.bp_method,
            ms_scaling_factor=self._config.ms_scaling_factor,
        )

        output = np.zeros(n, dtype=np.uint8)
        decimations = 0
        for _ in range(limit + 1):
            decoder.update_channel_probs(probabilities)
            output = np.asarray(decoder.decode(target), dtype=np.uint8)
            if self._is_valid(output, target):
                self.last_diagnostics = BpgdDiagnostics(
                    True,
                    False,
                    True,
                    decimations,
                    int(np.sum(frozen_values[frozen])),
                    int(np.sum(frozen)) - int(np.sum(frozen_values[frozen])),
                    0,
                )
                return tuple(int(bit) for bit in output)

            reliabilities = np.asarray(decoder.log_prob_ratios, dtype=float)
            candidates = np.flatnonzero(~frozen)
            if candidates.size == 0:
                break
            index = int(candidates[np.argmax(np.abs(reliabilities[candidates]))])
            hard_bit = int(reliabilities[index] < 0.0)
            probabilities[index] = (
                1.0 - self._config.freeze_epsilon
                if hard_bit
                else self._config.freeze_epsilon
            )
            frozen[index] = True
            frozen_values[index] = hard_bit
            decimations += 1

        residual_weight = int(np.sum(((self._parity_check @ output) & 1) ^ target))
        if self._config.syndrome_safe_fallback:
            fallback = self._bposd_decoder_type(
                self._parity_check,
                error_rate=self._config.error_rate,
                max_iter=self._config.max_iter,
                bp_method=self._config.bp_method,
                ms_scaling_factor=self._config.ms_scaling_factor,
                osd_method="osd_cs",
                osd_order=self._config.fallback_osd_order,
            )
            output = np.asarray(fallback.decode(target), dtype=np.uint8)
            valid = self._is_valid(output, target)
            self.last_diagnostics = BpgdDiagnostics(
                False,
                True,
                valid,
                decimations,
                int(np.sum(frozen_values[frozen])),
                int(np.sum(frozen)) - int(np.sum(frozen_values[frozen])),
                0 if valid else int(np.sum(((self._parity_check @ output) & 1) ^ target)),
            )
            return tuple(int(bit) for bit in output)

        self.last_diagnostics = BpgdDiagnostics(
            False,
            False,
            False,
            decimations,
            int(np.sum(frozen_values[frozen])),
            int(np.sum(frozen)) - int(np.sum(frozen_values[frozen])),
            residual_weight,
        )
        return tuple(int(bit) for bit in output)
