"""Tests for the A/B significance helper."""

import unittest

from eval.abstats import fisher_exact_two_tailed


class TestFisherExactTwoTailed(unittest.TestCase):
    """Reference values for the two-tailed Fisher exact test."""

    def test_fisher_matches_tea_tasting_reference(self):
        # Fisher's lady-tasting-tea table [[3, 1], [1, 3]] — published p = 0.4857.
        self.assertAlmostEqual(fisher_exact_two_tailed(3, 1, 1, 3), 0.4857, places=4)

    def test_fisher_matches_perfect_separation_reference(self):
        # [[5, 0], [0, 5]] — every control passed, every treatment failed. p = 2/252.
        self.assertAlmostEqual(fisher_exact_two_tailed(5, 0, 0, 5), 0.0079, places=4)

    def test_identical_arms_are_not_significant(self):
        # Same outcome in both arms — the tool must never suggest a difference.
        self.assertAlmostEqual(fisher_exact_two_tailed(4, 2, 4, 2), 1.0, places=4)


class TestObservedSessionData(unittest.TestCase):
    """Real measurements from the ponytail cycle, kept as worked examples.

    These document the sample sizes this harness actually produces, and why an
    eyeballed p-value is not good enough: the 15/18-vs-7/12 comparison was
    initially reported as ~0.11 by estimation. It is 0.21.
    """

    def test_step8_check_master_comparison_is_not_significant(self):
        # 3-all-complete: unmodified control 15/18 vs Step 8 build 7/12.
        self.assertAlmostEqual(fisher_exact_two_tailed(15, 3, 7, 5), 0.2098, places=4)

    def test_step9_do_master_comparison_is_not_significant(self):
        # 2-after-passing-test: interleaved control 6/6 vs step-9 build 5/6.
        self.assertAlmostEqual(fisher_exact_two_tailed(6, 0, 5, 1), 1.0, places=4)

    def test_six_pairs_cannot_detect_a_one_arm_difference(self):
        # The practical limit worth knowing before designing a run: at 6 pairs,
        # a single extra failure in one arm is indistinguishable from noise.
        self.assertGreater(fisher_exact_two_tailed(6, 0, 5, 1), 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
