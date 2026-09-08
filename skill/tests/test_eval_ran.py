"""Tests for distinguishing "the harness never ran" from "the scenario failed".

A shot that dies before reaching the API -- a missing build artifact, an absent
API key, a network failure -- produces no scored result, but the runner's exit
code is non-zero either way. Reported as a count, "did not pass" is then
indistinguishable from the model actually failing the scenario.

This is not hypothetical. The first eval run of #131's Step 0 reported
"5 shot(s); 5 did not pass" from a harness that never called the API once, and it
read exactly like a confirmed hypothesis. eval/README.md's whole thesis is that a
broken eval is self-sealing: nothing downstream contradicts it.

The reporter already holds the evidence -- a crashed shot writes a report whose
Summary table has a header, a separator, and no data rows -- so this is a pure
function over report text. It deliberately needs no API key, no network and no
live run, because it must work in exactly the conditions where the harness cannot.
"""

import unittest

from check_eval_ran import _read_reports, check_run, scored_scenarios

HEADER = (
    "# PDCA Eval Report — 2026-09-08 15:33:00\n\n"
    "## Summary\n\n"
    "| Scenario | Phase | Score | Threshold | GEval | Mechanical |\n"
    "|----------|-------|-------|-----------|-------|------------|\n"
)

EMPTY_REPORT = HEADER + "\n## Scenario Details\n"

SCORED_REPORT = (
    HEADER
    + "| 2-superpowers-branch-finish | TDD Implementation | 0.90 | 0.50 | ✅ | ✅ |\n"
    + "\n## Scenario Details\n"
)

TWO_SCORED = (
    HEADER
    + "| 2-first-step | TDD Implementation | 1.00 | 0.50 | ✅ | ✅ |\n"
    + "| 2-after-passing-test | TDD Implementation | 0.40 | 0.50 | ❌ | ✅ |\n"
    + "\n## Scenario Details\n"
)


class TestScoredScenarios(unittest.TestCase):
    def test_empty_report_has_no_scored_scenarios(self):
        """The signature of a shot that died before the API."""
        self.assertEqual(scored_scenarios(EMPTY_REPORT), [])

    def test_scored_report_names_its_scenario(self):
        self.assertEqual(scored_scenarios(SCORED_REPORT), ["2-superpowers-branch-finish"])

    def test_multiple_rows_all_counted(self):
        self.assertEqual(scored_scenarios(TWO_SCORED), ["2-first-step", "2-after-passing-test"])

    def test_a_failing_score_still_counts_as_scored(self):
        """A red verdict is a measurement. Only the absence of one is not."""
        self.assertIn("2-after-passing-test", scored_scenarios(TWO_SCORED))

    def test_separator_row_is_not_a_scenario(self):
        self.assertEqual(scored_scenarios(HEADER), [])

    def test_text_without_a_summary_table_scores_nothing(self):
        self.assertEqual(scored_scenarios("not a report at all"), [])


class TestCheckRun(unittest.TestCase):
    def test_reports_with_scores_pass(self):
        self.assertEqual(check_run([SCORED_REPORT]), [])

    def test_shots_that_scored_nothing_are_a_harness_error(self):
        problems = check_run([EMPTY_REPORT, EMPTY_REPORT])
        self.assertTrue(problems)
        joined = " ".join(problems)
        self.assertIn("did not run", joined)
        self.assertNotIn("did not pass", joined)

    def test_no_reports_at_all_is_a_harness_error(self):
        problems = check_run([])
        self.assertTrue(problems)
        self.assertIn("no report", " ".join(problems).lower())

    def test_one_scored_among_several_empty_is_not_a_harness_error(self):
        """A partial run still measured something; that is a scenario result, not a crash."""
        self.assertEqual(check_run([EMPTY_REPORT, SCORED_REPORT]), [])

    def test_problem_message_does_not_imply_a_verdict(self):
        """The failure text must not read like the model failed the scenario.

        "scored scenario" is fine and necessary -- the absence of a score is the
        whole signal. What must not appear is language asserting an outcome the
        run never produced.
        """
        joined = " ".join(check_run([EMPTY_REPORT])).lower()
        for verdict_phrase in ("failed the scenario", "did not pass", "scenario failed"):
            self.assertNotIn(verdict_phrase, joined)
        self.assertIn("did not run", joined)


class TestReadReports(unittest.TestCase):
    """Callers must be able to pass only this run's reports.

    eval/results/ accumulates across runs, so passing the whole directory would let a
    previously scored report mask a current run that scored nothing -- exactly the
    stale-artifact hazard that made a build look correct by accident in #114.
    """

    def test_reads_a_directory_and_a_single_file(self):
        import tempfile
        from pathlib import Path as P

        with tempfile.TemporaryDirectory() as d:
            root = P(d)
            (root / "a.md").write_text(SCORED_REPORT)
            (root / "b.md").write_text(EMPTY_REPORT)

            self.assertEqual(len(_read_reports([str(root)])), 2)
            self.assertEqual(_read_reports([str(root / "b.md")]), [EMPTY_REPORT])
            # only the empty one -> harness error, despite a scored sibling on disk
            self.assertTrue(check_run(_read_reports([str(root / "b.md")])))

    def test_missing_path_is_ignored_not_fatal(self):
        self.assertEqual(_read_reports(["/nonexistent/path.md"]), [])


if __name__ == "__main__":
    unittest.main()
