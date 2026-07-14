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


class BpgdAdapter:
    """Binary BP-guided-decimation research implementation.

    Repeatedly runs BP, checks for a syndrome-matching correction, and when BP
    does not converge freezes the most reliable undecimated variable to its
    current hard decision before restarting BP. This follows the central binary
    BPGD procedure described by Yao et al., but is an independent implementation
    and must not be represented as author-verified until checked line-by-line
    against the final paper version or official code.
    """

    def __init__(self, parity_check: Sequence[Sequence[int]], config: BpgdConfig):
        if not 0.0 < config.error_rate < 1.0:
            raise ValueError("error_rate must be between 0 and 1")
        if not 0.0 < config.freeze_epsilon < 0.5:
            raise ValueError("freeze_epsilon must be between 0 and 0.5")
        try:
            from ldpc import BpDecoder  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the pinned `ldpc` package before using BpgdAdapter") from exc

        self._bp_decoder_type = BpDecoder
        self._parity_check = np.asarray(parity_check, dtype=np.uint8)
        self._config = config
        self.last_decimations = 0

    def decode(self, syndrome: Sequence[int]) -> tuple[int, ...]:
        target = np.asarray(syndrome, dtype=np.uint8)
        n = self._parity_check.shape[1]
        probabilities = np.full(n, self._config.error_rate, dtype=float)
        frozen = np.zeros(n, dtype=bool)
        limit = self._config.decimation_limit or n

        decoder = self._bp_decoder_type(
            self._parity_check,
            error_rate=self._config.error_rate,
            max_iter=self._config.max_iter,
            bp_method=self._config.bp_method,
            ms_scaling_factor=self._config.ms_scaling_factor,
        )

        self.last_decimations = 0
        output = np.zeros(n, dtype=np.uint8)
        for _ in range(limit + 1):
            decoder.update_channel_probs(probabilities)
            output = np.asarray(decoder.decode(target), dtype=np.uint8)
            if np.array_equal((self._parity_check @ output) & 1, target):
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
            self.last_decimations += 1

        return tuple(int(bit) for bit in output)
