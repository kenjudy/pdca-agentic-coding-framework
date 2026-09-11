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


class TestRubricDecomposition(unittest.TestCase):
    """Rubrics must expose their criteria as addressable items (#148).

    `_rubric_for_prompt(prompt_id)` in tests/test_evals.py returns one monolithic CRITERIA
    string per phase, so every scenario in a phase is scored against every criterion in it
    -- including ones the scenario does not claim to measure. eval/README.md's materiality
    rule forbids exactly that when a human reads a failure; nothing binds the judge.

    Measured instances: rubric 2 docking 2-superpowers-tdd-precedence for test ordering it
    never claimed (#136), rubric 4 on 4-tdd-breakdown (#151), rubric 3 on 3-all-complete
    (#111), and 2-skip-tests-request carrying skip_geval because the rubric cannot score a
    correct refusal. skip_geval is the only existing lever and it is all-or-nothing.

    This is phase 1: PURE DECOMPOSITION. The assembled prompt must be byte-identical to
    the string that shipped before it, so no eval spend is needed to show behaviour is
    unchanged, and any later score movement is attributable to scoping alone rather than
    to rewording. Per-scenario selection lands separately.

    Out-of-scope criteria will be OMITTED from the assembled text, never named. #149
    measured the alternative twice: a "do not penalise X" clause reliably becomes
    "penalise X", and both attempts made scores worse.
    """

    RUBRICS = ("1a", "1b", "2", "3", "4")

    @staticmethod
    def _snapshot():
        import json
        from pathlib import Path

        return json.loads(
            (Path(__file__).parent / "fixtures" / "rubric_criteria_snapshot.json").read_text()
        )

    def test_every_rubric_exposes_addressable_criteria_items(self):
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                items = getattr(module, "CRITERIA_ITEMS", None)
                self.assertIsInstance(
                    items,
                    dict,
                    f"rubric_{name} has no CRITERIA_ITEMS mapping, so a scenario cannot "
                    "name which criteria apply to it and skip_geval remains the only lever",
                )
                self.assertTrue(items, f"rubric_{name}.CRITERIA_ITEMS is empty")

    def test_assembled_criteria_is_byte_identical_to_the_published_string(self):
        """The whole safety argument for phase 1. If assembly reproduces the prior text
        exactly, decomposition provably changed no behaviour and costs no API spend to
        verify."""
        snapshot = self._snapshot()
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                self.assertEqual(
                    module.CRITERIA,
                    snapshot[name]["criteria"],
                    f"rubric_{name}'s assembled CRITERIA differs from the text that shipped "
                    "before decomposition -- phase 1 must be behaviour-neutral",
                )

    def test_thresholds_are_unchanged(self):
        snapshot = self._snapshot()
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                self.assertEqual(module.THRESHOLD, snapshot[name]["threshold"])


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

    @staticmethod
    def _bands_as_written(criteria: str) -> list[float]:
        marker = "Then assign a score on a scale of 0 to 1:"
        ladder = criteria[criteria.index(marker):]
        return [float(m) for m in re.findall(r"^(\d\.\d+) —", ladder, re.M)]

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

    def test_bands_appear_in_descending_order_as_written(self):
        """#171 critic pass: `_bands()` sorts, so a band physically misplaced in the
        ladder (e.g. written after 0.0 instead of between 0.7 and 0.4) still satisfies
        the two tests above. The judge reads the ladder top-down as written; it must
        itself be in descending order, not just contain the right values."""
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                ordered = self._bands_as_written(module.CRITERIA)
                self.assertEqual(
                    ordered,
                    sorted(ordered, reverse=True),
                    f"rubric_{name}'s bands {ordered} are not in descending order as written",
                )

    def test_the_0_6_band_text_is_identical_across_all_rubrics(self):
        """The PR's stated safety property: identical wording across all five rubrics so
        no phase-specific vocabulary is introduced for the judge to score against (#149).
        Nothing previously enforced this -- a future reword of one rubric's band would
        drift silently, and the byte-identity snapshot test's prescribed remedy for any
        CRITERIA change (regenerate the snapshot) would rubber-stamp exactly that drift."""
        texts = {}
        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            match = re.search(r"^0\.6 —.*?(?=\n\n0\.4 —)", module.CRITERIA, re.S | re.M)
            self.assertIsNotNone(match, f"rubric_{name} has no 0.6 band block")
            texts[name] = match.group(0)
        self.assertEqual(
            len(set(texts.values())),
            1,
            f"0.6 band text differs across rubrics: {texts}",
        )
