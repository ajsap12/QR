from __future__ import annotations

import unittest

import numpy as np

from bb_code import published_144_12_instance
from logical import classify_x_residual, is_in_rowspace


class LogicalClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        code = published_144_12_instance()
        self.hx = np.asarray(code.hx, dtype=np.uint8)
        self.hz = np.asarray(code.hz, dtype=np.uint8)

    def test_zero_residual_is_stabilizer(self) -> None:
        residual = np.zeros(self.hx.shape[1], dtype=np.uint8)
        self.assertEqual(classify_x_residual(residual, self.hx, self.hz), "stabilizer")

    def test_x_stabilizer_row_is_stabilizer(self) -> None:
        residual = self.hx[0].copy()
        self.assertTrue(is_in_rowspace(residual, self.hx))
        self.assertEqual(classify_x_residual(residual, self.hx, self.hz), "stabilizer")

    def test_single_bit_with_nonzero_syndrome_is_syndrome_failure(self) -> None:
        residual = np.zeros(self.hx.shape[1], dtype=np.uint8)
        residual[0] = 1
        self.assertEqual(classify_x_residual(residual, self.hx, self.hz), "syndrome_failure")


if __name__ == "__main__":
    unittest.main()
