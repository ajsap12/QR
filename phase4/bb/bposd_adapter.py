from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class BpOsdConfig:
    error_rate: float
    max_iter: int = 100
    bp_method: str = "ms"
    ms_scaling_factor: float = 0.0
    osd_method: str = "osd_cs"
    osd_order: int = 7


class BpOsdAdapter:
    """Thin adapter around the Roffe et al. `ldpc` package BpOsdDecoder.

    This preserves the package's native decoding algorithm while normalizing the
    constructor and decode interface used by this research lab.
    """

    def __init__(self, parity_check: Sequence[Sequence[int]], config: BpOsdConfig):
        if not 0.0 < config.error_rate < 1.0:
            raise ValueError("error_rate must be between 0 and 1")
        try:
            import numpy as np
            from ldpc import BpOsdDecoder  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Install pinned dependencies before using BpOsdAdapter"
            ) from exc

        self._np = np
        self._parity_check = np.asarray(parity_check, dtype=np.uint8)
        self._config = config
        self._decoder: Any = BpOsdDecoder(
            self._parity_check,
            error_rate=config.error_rate,
            max_iter=config.max_iter,
            bp_method=config.bp_method,
            ms_scaling_factor=config.ms_scaling_factor,
            osd_method=config.osd_method,
            osd_order=config.osd_order,
        )

    def decode(self, syndrome: Sequence[int]) -> tuple[int, ...]:
        syndrome_array = self._np.asarray(syndrome, dtype=self._np.uint8)
        result = self._decoder.decode(syndrome_array)
        return tuple(int(bit) & 1 for bit in result)
