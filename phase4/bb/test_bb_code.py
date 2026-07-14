from __future__ import annotations

import unittest

from bb_code import css_commutes, published_144_12_instance


class PublishedBBCodeTests(unittest.TestCase):
    def test_published_144_12_structure(self) -> None:
        code = published_144_12_instance()
        self.assertEqual(code.n, 144)
        self.assertEqual(code.k, 12)
        self.assertEqual(len(code.hx), 72)
        self.assertEqual(len(code.hz), 72)
        self.assertTrue(css_commutes(code.hx, code.hz))
        self.assertEqual(set(code.x_check_weights), {6})
        self.assertEqual(set(code.z_check_weights), {6})

    def test_polynomial_terms_match_publication(self) -> None:
        code = published_144_12_instance()
        self.assertEqual(code.a_terms, ((3, 0), (0, 1), (0, 2)))
        self.assertEqual(code.b_terms, ((0, 3), (1, 0), (2, 0)))


if __name__ == "__main__":
    unittest.main()
