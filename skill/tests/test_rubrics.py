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
        marker = "Then assign a score on a scale of 0 to 1"
        ladder = criteria[criteria.index(marker):]
        return sorted(float(m) for m in re.findall(r"^(\d\.\d+) —", ladder, re.M))

    @staticmethod
    def _bands_as_written(criteria: str) -> list[float]:
        marker = "Then assign a score on a scale of 0 to 1"
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
            assert match is not None, f"rubric_{name} has no 0.6 band block"
            texts[name] = match.group(0)
        self.assertEqual(
            len(set(texts.values())),
            1,
            f"0.6 band text differs across rubrics: {texts}",
        )


class TestCriteriaSelection(unittest.TestCase):
    """A scenario may narrow the criteria it is judged against (#148 phase 2).

    Out-of-scope criteria are OMITTED from the assembled text, never named. #149 measured
    the alternative twice on rubric 2: a "do not penalise X" clause reliably becomes
    "penalise X", and both attempts drove scores down rather than sideways.

    Numbering stays contiguous over whatever subset is passed, so the judge never sees a
    gap that implies something was withheld.
    """

    ITEMS = {"alpha": "First criterion.", "beta": "Second criterion.", "gamma": "Third criterion."}

    def test_selection_renumbers_contiguously(self):
        from eval.rubrics.assemble import assemble

        out = assemble("P:\n", self.ITEMS, "TAIL", selected=["alpha", "gamma"])
        self.assertEqual(out, "P:\n  1. First criterion.\n  2. Third criterion.\nTAIL")

    def test_selection_follows_rubric_order_not_caller_order(self):
        """Otherwise the same subset renders two different prompts depending on how a
        scenario happened to list its ids, and two scenarios' scores stop being
        comparable."""
        from eval.rubrics.assemble import assemble

        forward = assemble("P:\n", self.ITEMS, "T", selected=["alpha", "beta"])
        reversed_ = assemble("P:\n", self.ITEMS, "T", selected=["beta", "alpha"])
        self.assertEqual(forward, reversed_)

    def test_unknown_criteria_id_raises(self):
        """A typo must fail loudly. Silently ignoring it would either score against every
        criterion or against none, and both look like a normal result in the report."""
        from eval.rubrics.assemble import UnknownCriterion, assemble

        with self.assertRaises(UnknownCriterion) as ctx:
            assemble("P:\n", self.ITEMS, "T", selected=["alpha", "delta"])
        self.assertIn("delta", str(ctx.exception))

    def test_empty_selection_raises(self):
        """Selecting nothing is not scoping, it is skip_geval with extra steps -- and it
        would hand the judge a rubric with no criteria at all."""
        from eval.rubrics.assemble import assemble

        with self.assertRaises(ValueError):
            assemble("P:\n", self.ITEMS, "T", selected=[])


class TestRubricForScenario(unittest.TestCase):
    """The harness must key the rubric on the scenario, not only on the phase.

    tests/test_evals.py is excluded from the default suite, so selection logic living
    there would be untested everywhere. It lives in eval.rubrics instead, where it runs on
    every push.
    """

    def test_unscoped_scenario_gets_the_whole_rubric(self):
        from eval.rubrics import rubric_2, rubric_for_scenario

        criteria, threshold = rubric_for_scenario("2", {})
        self.assertEqual(criteria, rubric_2.CRITERIA)
        self.assertEqual(threshold, rubric_2.THRESHOLD)

    def test_scoped_scenario_gets_only_the_named_criteria(self):
        from eval.rubrics import rubric_2, rubric_for_scenario

        criteria, _ = rubric_for_scenario("2", {"geval_criteria": ["called-shot"]})
        self.assertIn(rubric_2.CRITERIA_ITEMS["called-shot"], criteria)
        self.assertNotIn(rubric_2.CRITERIA_ITEMS["degenerate-first"], criteria)

    def test_omitted_criteria_are_not_mentioned_at_all(self):
        """The #149 constraint, asserted rather than trusted: an omitted criterion must
        leave no trace in the prompt for the judge to score against."""
        from eval.rubrics import rubric_2, rubric_for_scenario

        criteria, _ = rubric_for_scenario("2", {"geval_criteria": ["called-shot"]})
        for dropped in ("degenerate-first", "stub-discipline", "refuse-to-skip-tests"):
            with self.subTest(dropped=dropped):
                self.assertNotIn(rubric_2.CRITERIA_ITEMS[dropped], criteria)

    def test_unknown_prompt_id_still_raises(self):
        from eval.rubrics import rubric_for_scenario

        with self.assertRaises(ValueError):
            rubric_for_scenario("99", {})

    def test_scoped_criteria_leave_no_trace_in_bands_or_scaffold(self):
        """The exact defect that sank the first #148 phase-2 attempt (12ad72e): scoping
        the numbered list removed a criterion's own text, but its concept still appeared
        in the scoring bands and Strengths/Weaknesses scaffold under different wording --
        "stub implementation contains conditional logic" in the 0.4 band, for example,
        with no "stub-discipline" criterion in scope to license it. A scenario scoped to
        only "called-shot" must not be judged against "stub" or "happy path" anywhere in
        the assembled prompt, not just absent from the numbered list. ("degenerate" is
        deliberately not checked here -- it legitimately appears inside the "called-shot"
        item's own text, describing what "Why this test first" should cite.)"""
        from eval.rubrics import rubric_for_scenario

        criteria, _ = rubric_for_scenario("2", {"geval_criteria": ["called-shot"]})
        lowered = criteria.lower()
        for leaked_concept in ("stub", "happy path"):
            with self.subTest(concept=leaked_concept):
                self.assertNotIn(leaked_concept, lowered)


class TestEveryRubricUsesTheSharedGenericTail(unittest.TestCase):
    """Every rubric's TAIL must contain GENERIC_TAIL verbatim (#148).

    Scoping only works because the scaffold and bands never name a specific criterion --
    they say "the criteria listed above" instead. That property holds only as long as
    every rubric actually uses the shared GENERIC_TAIL string; a future edit that inlines
    a rubric-specific tweak into one rubric's own TAIL would silently reintroduce the exact
    defect #148 exists to fix, without the string-literal snapshot test (which only proves
    *some* text changed, not that it changed the right way) catching it.
    """

    RUBRICS = ("1a", "1b", "2", "3", "4")

    def test_generic_tail_is_present_verbatim_in_every_rubric(self):
        from eval.rubrics.generic_tail import GENERIC_TAIL

        for name in self.RUBRICS:
            module = importlib.import_module(f"eval.rubrics.rubric_{name}")
            with self.subTest(rubric=name):
                self.assertIn(
                    GENERIC_TAIL,
                    module.CRITERIA,
                    f"rubric_{name} does not contain GENERIC_TAIL verbatim -- its scaffold "
                    "or bands may have drifted into rubric-specific wording again",
                )
