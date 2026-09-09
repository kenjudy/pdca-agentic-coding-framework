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
