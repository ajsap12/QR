from __future__ import annotations

import unittest

import numpy as np

from bb_code import published_72_12_instance
from stateful_sum_product import StatefulSumProductBpgd


class StatefulSumProductTests(unittest.TestCase):
    def test_zero_syndrome_converges_without_decimation(self) -> None:
        code = published_72_12_instance()
        h = np.asarray(code.hz, dtype=np.uint8)
        decoder = StatefulSumProductBpgd(h, 0.04, iterations_per_round=5)
        syndrome = np.zeros(h.shape[0], dtype=np.uint8)
        correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
        self.assertTrue(decoder.last_diagnostics.converged)
        self.assertEqual(decoder.last_diagnostics.decimations, 0)
        self.assertTrue(np.array_equal((h @ correction) & 1, syndrome))

    def test_single_sample_returns_binary_vector(self) -> None:
        code = published_72_12_instance()
        h = np.asarray(code.hz, dtype=np.uint8)
        rng = np.random.default_rng(20260714)
        error = (rng.random(code.n) < 0.04).astype(np.uint8)
        syndrome = (h @ error) & 1
        decoder = StatefulSumProductBpgd(h, 0.04, iterations_per_round=20)
        correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
        self.assertEqual(correction.shape, (code.n,))
        self.assertTrue(np.all((correction == 0) | (correction == 1)))


if __name__ == "__main__":
    unittest.main()
