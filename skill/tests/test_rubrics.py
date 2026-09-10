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
