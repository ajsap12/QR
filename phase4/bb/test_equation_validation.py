from __future__ import annotations

import math
import unittest

import numpy as np

from equation_validation import (
    channel_llr,
    check_message,
    hard_decision,
    one_flooding_iteration,
    posterior_llr,
    reliability,
    variable_message,
)


class EquationValidationTests(unittest.TestCase):
    def test_channel_llr(self) -> None:
        self.assertAlmostEqual(channel_llr(0.1), math.log(9.0), places=12)

    def test_check_message_even_syndrome_degree_two(self) -> None:
        incoming = math.log(9.0)
        self.assertAlmostEqual(check_message([incoming], 0), incoming, places=12)

    def test_check_message_odd_syndrome_flips_sign(self) -> None:
        incoming = math.log(9.0)
        self.assertAlmostEqual(check_message([incoming], 1), -incoming, places=12)

    def test_variable_update_excludes_target_edge(self) -> None:
        self.assertAlmostEqual(variable_message(2.0, [0.5, -0.25]), 2.25)

    def test_posterior_includes_all_incoming_checks(self) -> None:
        self.assertAlmostEqual(posterior_llr(2.0, [0.5, -0.25, 1.0]), 3.25)

    def test_hard_decision_sign_convention(self) -> None:
        self.assertEqual(hard_decision(0.1), 0)
        self.assertEqual(hard_decision(-0.1), 1)
        self.assertEqual(hard_decision(0.0), 0)

    def test_reliability_is_absolute_posterior_llr(self) -> None:
        self.assertEqual(reliability(-3.5), 3.5)
        self.assertEqual(reliability(3.5), 3.5)

    def test_one_check_even_syndrome_hand_calculation(self) -> None:
        result = one_flooding_iteration([[1, 1]], [0], 0.1)
        expected = 2.0 * math.log(9.0)
        np.testing.assert_allclose(result.posterior_llr, [expected, expected], rtol=0, atol=1e-12)
        np.testing.assert_array_equal(result.hard_decision, [0, 0])

    def test_one_check_odd_syndrome_tie_case(self) -> None:
        result = one_flooding_iteration([[1, 1]], [1], 0.1)
        np.testing.assert_allclose(result.posterior_llr, [0.0, 0.0], rtol=0, atol=1e-12)
        np.testing.assert_array_equal(result.hard_decision, [0, 0])


if __name__ == "__main__":
    unittest.main()
