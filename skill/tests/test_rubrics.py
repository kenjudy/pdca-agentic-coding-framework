"""Constraints on the LLM-as-judge rubrics themselves.

A rubric is the measuring instrument. When it is wrong, every scenario it scores is
wrong in the same direction at once, and the failure looks like flaky scenarios rather
than a broken instrument -- which is how issue #136 presented.
"""

import unittest

from eval.rubrics import rubric_2


class TestRubric2DoesNotDemandTheImpossible(unittest.TestCase):
    """The judge must not penalise the model for not executing tests.

    The eval harness sends one prompt and records one response. There is no tool access,
    no filesystem and no test runner, so the model *cannot* run anything. But the DO
    master prompt it is given says "Run the test. If actual failure != expected failure
    -- STOP." ("2. Do/2. Test Drive the Change.md:48"), and the judge reads that prompt
    as part of the input.

    Measured on run 34275465380 (10 shots, unmodified master): the judge imported that
    line as a scoring criterion nowhere present in this rubric, and docked responses for
    it in 9 of 13 sub-threshold shots -- while affirming in those same reasons that all
    four called-shot fields were present. Mechanical checks passed 17 of 18. Scores came
    out bimodal with an empty band across the 0.50 threshold (13 shots at 0.20-0.40, 5 at
    0.70-0.90, none at 0.50 or 0.60): the signature of a judge flipping between two
    readings, not of a model behaving variably.

    The rubric's own bands never mention execution, so a response with all four fields,
    correct ordering and clean stub discipline scores 1.0 by the band text. Several
    scored 0.20.
    """

    def test_criteria_tells_the_judge_the_response_cannot_execute_anything(self):
        self.assertTrue(
            "no tool access" in rubric_2.CRITERIA,
            "rubric_2 does not tell the judge the response is a single turn with no tool "
            "access, so the judge scores the model against 'Run the test' from the DO "
            "master prompt -- an action the harness makes impossible",
        )

    def test_criteria_forbids_penalising_absent_test_execution(self):
        self.assertTrue(
            "Do NOT penalise" in rubric_2.CRITERIA,
            "rubric_2 never forbids docking a response for not running the test, which is "
            "the criterion the judge invented in 9 of 13 sub-threshold shots on run "
            "34275465380",
        )

    def test_criteria_forbids_penalising_a_request_to_read_state_first(self):
        """Reading a file before editing it is what the framework mandates -- CLAUDE.md's
        'Verify state before acting'. The judge docked responses for doing it."""
        self.assertTrue(
            "asking to see a file" in rubric_2.CRITERIA,
            "rubric_2 does not protect the framework-mandated behaviour of inspecting "
            "state before editing, which the judge scored as a process delay",
        )


if __name__ == "__main__":
    unittest.main()


class TestRubric2OrderingIsReconciled(unittest.TestCase):
    """The scoring bands must not contradict the criteria above them.

    Measured on run 34372905517 (10 shots against the harness-constraint fix): the
    non-execution complaint fell from 9/13 to 5/14 of sub-threshold shots, but scores
    barely moved -- 14/23 still below threshold -- because a second off-criteria
    complaint replaced it. 9 of 14 low shots were docked for test ORDERING, and the
    docks contradicted each other: one penalised writing the present-header test first
    ("does not begin with the degenerate case"), another penalised writing the
    degenerate case first ("the stub already satisfies it, making it vacuously pass").

    Both are in the rubric. Neither is ranked. The DO master reconciles them and the
    rubric dropped the reconciliation -- "2. Do/2. Test Drive the Change.md:60": "If the
    next test in sequence would pass trivially against the current stub (vacuous green),
    skip to the first test the stub cannot satisfy -- that is the genuine RED."

    The scenario's stub is `return 0`, which already satisfies the absent-header case,
    so the master's answer is present-header first. The rubric's band 1.0 requires
    "starts with degenerate/zero case" flatly, and band 0.4 penalises "starts with happy
    path". The model follows the master and is scored against a rubric missing the rule
    that makes it correct.
    """

    @staticmethod
    def _bands() -> str:
        """Just the scoring ladder -- the operative, last-read part of the rubric."""
        marker = "Then assign a score on a scale of 0 to 1:"
        return rubric_2.CRITERIA[rubric_2.CRITERIA.index(marker):]

    def test_criteria_states_the_vacuous_green_override(self):
        self.assertTrue(
            "the stub cannot satisfy" in rubric_2.CRITERIA,
            "rubric_2 never states the master's tie-breaker -- that a degenerate case "
            "already satisfied by the stub must be skipped for the first test the stub "
            "cannot satisfy -- so the judge applies 'degenerate first' unconditionally",
        )

    def test_bands_do_not_demand_degenerate_first_unconditionally(self):
        """Prose above the ladder does not move scores; the ladder does. The harness
        constraint added in the previous commit sat above bands that contradicted it,
        which is why it moved its target complaint without moving the distribution."""
        self.assertFalse(
            "starts with degenerate/zero case" in self._bands(),
            "band 1.0 still requires starting with the degenerate case unconditionally, "
            "contradicting the vacuous-green override stated in the criteria above it",
        )

    def test_a_band_exists_across_the_threshold(self):
        """Bands were 1.0 / 0.7 / 0.4 / 0.0 against a 0.50 threshold: the two nearest
        anchors straddle it with nothing between, so a borderline response has no band
        to land on and is pushed to one side."""
        bands = self._bands()
        self.assertTrue(
            "\n0.6 —" in bands or "\n0.5 —" in bands,
            "no scoring band sits between 0.4 and 0.7, so the ladder itself pushes "
            "borderline responses away from the 0.50 threshold in both directions",
        )

    def test_happy_path_is_not_used_as_a_bare_synonym_for_non_degenerate(self):
        """In this scenario the present-header case IS the forcing test -- the one the
        stub cannot satisfy -- yet the rubric's vocabulary lets it be described as a
        'happy path' violation."""
        self.assertTrue(
            "forcing test" in rubric_2.CRITERIA,
            "rubric_2 has no term for 'the first test the stub cannot satisfy', so the "
            "correct answer remains describable as a happy-path violation",
        )
