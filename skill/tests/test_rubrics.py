"""Constraints on the LLM-as-judge rubrics themselves.

A rubric is the measuring instrument. When it is wrong, every scenario it scores is wrong
in the same direction at once, and the failure looks like flaky scenarios rather than a
broken instrument -- which is how issue #136 presented.

Two rounds of prose edits to rubric_2 were measured and REVERTED (see #136): telling the
judge what not to penalise made those things salient and it penalised them harder. Assert
what the rubric must not SAY, sparingly; do not assume an added instruction will be obeyed.
"""

import importlib
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
