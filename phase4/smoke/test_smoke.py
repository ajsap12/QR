from __future__ import annotations

import unittest

from phase4_smoke.core import syndrome, xor_bits
from phase4_smoke.decoders import exhaustive_min_weight_decode, greedy_bit_flip_decode


H_REPETITION = (
    (1, 1, 0),
    (0, 1, 1),
)


class SmokeTests(unittest.TestCase):
    def test_zero_error(self) -> None:
        self.assertEqual(syndrome(H_REPETITION, (0, 0, 0)), (0, 0))

    def test_reference_decoder_corrects_all_single_bit_errors(self) -> None:
        for error in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            syn = syndrome(H_REPETITION, error)
            correction = exhaustive_min_weight_decode(H_REPETITION, syn)
            self.assertEqual(syndrome(H_REPETITION, correction), syn)

    def test_greedy_decoder_interface(self) -> None:
        syn = syndrome(H_REPETITION, (1, 0, 0))
        correction = greedy_bit_flip_decode(H_REPETITION, syn)
        self.assertEqual(xor_bits(syndrome(H_REPETITION, correction), syn), (0, 0))

    def test_bad_dimensions_raise(self) -> None:
        with self.assertRaises(ValueError):
            syndrome(((1, 0),), (1, 0, 1))


if __name__ == "__main__":
    unittest.main()
