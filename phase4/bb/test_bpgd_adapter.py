from __future__ import annotations

import unittest

import numpy as np

from bb_code import published_72_12_instance
from bpgd_adapter import BpgdAdapter, BpgdConfig


class BpgdAdapterTests(unittest.TestCase):
    def test_zero_syndrome_decodes_to_valid_correction(self) -> None:
        code = published_72_12_instance()
        hz = np.asarray(code.hz, dtype=np.uint8)
        decoder = BpgdAdapter(hz, BpgdConfig(error_rate=0.04))
        syndrome = np.zeros(hz.shape[0], dtype=np.uint8)
        correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
        self.assertTrue(np.array_equal((hz @ correction) & 1, syndrome))

    def test_single_sample_returns_binary_vector(self) -> None:
        code = published_72_12_instance()
        hz = np.asarray(code.hz, dtype=np.uint8)
        rng = np.random.default_rng(20260714)
        error = (rng.random(code.n) < 0.04).astype(np.uint8)
        syndrome = (hz @ error) & 1
        decoder = BpgdAdapter(hz, BpgdConfig(error_rate=0.04))
        correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
        self.assertEqual(correction.shape, (code.n,))
        self.assertTrue(np.all((correction == 0) | (correction == 1)))


if __name__ == "__main__":
    unittest.main()
