from __future__ import annotations

import unittest

from bb_code import published_primary_panel


class PublishedPanelTests(unittest.TestCase):
    def test_published_dimensions_and_encoded_qubits(self) -> None:
        expected = {
            "[[72,12,6]]": (72, 12),
            "[[108,8,10]]": (108, 8),
            "[[144,12,12]]": (144, 12),
        }
        for label, code in published_primary_panel():
            self.assertEqual((code.n, code.k), expected[label])
            self.assertTrue(all(weight == 6 for weight in code.x_check_weights))
            self.assertTrue(all(weight == 6 for weight in code.z_check_weights))


if __name__ == "__main__":
    unittest.main()
