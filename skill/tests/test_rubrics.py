"""Constraints on the LLM-as-judge rubrics themselves.

A rubric is the measuring instrument. When it is wrong, every scenario it scores is wrong
in the same direction at once, and the failure looks like flaky scenarios rather than a
broken instrument -- which is how issue #136 presented.

Two rounds of prose edits to rubric_2 were measured and REVERTED (see #136): telling the
judge what not to penalise made those things salient and it penalised them harder. Assert
what the rubric must not SAY, sparingly; do not assume an added instruction will be obeyed.
"""

import importlib
import re
import unittest

from eval.rubrics import rubric_2


class TestRubric2DoesNotReintroduceTheBareCompleteStem(unittest.TestCase):
    """#112 removed the bare stem "complete" from the mechanical matcher because it
    matched the ordinary adjective -- "here's the complete sequence" is the behavior the
    prompt asks for, and the check scored it as a violation. The rubric prose still quoted
    the bare words, so the judge could dock what the mechanical tier was fixed to stop
    docking, one tier up and invisibly.

    Unmeasured against the judge: found by reading the rubric, not by a failing shot.
    """

    def test_bands_do_not_penalise_the_bare_word_complete(self):
        self.assertFalse(
            "declares the work complete" in rubric_2.CRITERIA,
            "band 0.0 penalises 'declares the work complete', reintroducing in the judge "
            "the bare-stem match that #112 removed from the mechanical tier",
        )


if __name__ == "__main__":
    unittest.main()


class TestScoringBandsSpanTheThreshold(unittest.TestCase):
    """Every rubric's bands must include an anchor across the decision boundary (#153).

    All five rubrics define 1.0 / 0.7 / 0.4 / 0.0 against THRESHOLD = 0.5, so the two
    nearest anchors straddle the threshold with nothing between them. A response the judge
    considers neither "mostly compliant" nor "partially compliant" has no band to land on
    and is pushed to one side, close to arbitrarily -- which converts a small judgment
    difference into a pass/fail flip and presents as scenario flakiness.

    The pre-fix #136 distribution had 13 shots at 0.20-0.40, 5 at 0.70-0.90, and nothing at
    0.50 or 0.60. That hole was first read as pure judge instability; it is at least partly
    the ladder's shape.

    This asserts structure, not wording: a band strictly between the 0.4 and 0.7 anchors,
    at or above each rubric's own threshold, so that "violates no hard constraint" can land
    on the passing side.
    """

    RUBRICS = ("1a", "1b", "2", "3", "4")

    @staticmethod
    def _bands(criteria: str) -> list[float]:
        marker = "Then assign a score on a scale of 0 to 1:"
        ladder = criteria[criteria.index(marker):]
        return sorted(float(m) for m in re.findall(r"^(\d\.\d+) —", ladder, re.M))

    def test_every_rubric_has_a_band_between_0_4_and_0_7(self):
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                bands = self._bands(module.CRITERIA)
                spanning = [b for b in bands if 0.4 < b < 0.7]
                self.assertTrue(
                    spanning,
                    f"rubric_{name} bands are {bands} with threshold {module.THRESHOLD}: "
                    "nothing sits between 0.4 and 0.7, so a borderline response has no band "
                    "to land on and is pushed across the threshold in one direction or the "
                    "other",
                )

    def test_the_spanning_band_is_not_below_its_rubrics_threshold(self):
        """The band exists so that violating no hard constraint can PASS. One placed below
        the threshold would relabel the same failure rather than fix the gap."""
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                spanning = [b for b in self._bands(module.CRITERIA) if 0.4 < b < 0.7]
                self.assertTrue(
                    spanning and max(spanning) >= module.THRESHOLD,
                    f"rubric_{name}'s spanning band {spanning} is below its threshold "
                    f"{module.THRESHOLD}",
                )
