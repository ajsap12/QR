from __future__ import annotations

import unittest

import numpy as np

from bb_code import published_72_12_instance
from bpgd_adapter import BpgdAdapter, BpgdConfig


class BpgdDiagnosticsTests(unittest.TestCase):
    def test_zero_syndrome_reports_valid_diagnostics(self) -> None:
        code = published_72_12_instance()
        h = np.asarray(code.hz, dtype=np.uint8)
        decoder = BpgdAdapter(h, BpgdConfig(error_rate=0.04))
        syndrome = np.zeros(h.shape[0], dtype=np.uint8)
        correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
        self.assertTrue(decoder.last_diagnostics.syndrome_valid)
        self.assertTrue(np.array_equal((h @ correction) & 1, syndrome))

    def test_fallback_can_be_disabled_for_diagnostics(self) -> None:
        code = published_72_12_instance()
        h = np.asarray(code.hz, dtype=np.uint8)
        decoder = BpgdAdapter(
            h,
            BpgdConfig(error_rate=0.04, decimation_limit=0, syndrome_safe_fallback=False),
        )
        syndrome = np.zeros(h.shape[0], dtype=np.uint8)
        decoder.decode(syndrome)
        self.assertFalse(decoder.last_diagnostics.fallback_used)


if __name__ == "__main__":
    unittest.main()
