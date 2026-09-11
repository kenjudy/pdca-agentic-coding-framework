"""Tests for the mechanical assertion checker."""

import unittest

from eval.mechanical import check_mechanical

EMPTY_SIGNALS = {
    "must_contain": [],
    "must_not_contain": [],
    "called_shot_required": False,
}

# Called shot output with all four required fields
CALLED_SHOT_FULL = """
- **Test name:** test_rejects_empty_input
- **Behavior under test:** validate_scenario({}) raises ScenarioValidationError
- **Expected failure:** AssertionError: ScenarioValidationError not raised
- **Why this test first:** degenerate case — establishes that the API rejects empty input before testing valid inputs
"""

# Called shot output missing the Expected failure field
CALLED_SHOT_MISSING_EXPECTED_FAILURE = """
- **Test name:** test_rejects_empty_input
- **Behavior under test:** validate_scenario({}) raises ScenarioValidationError
"""

# All four fields present, but bolded with the colon outside the emphasis
CALLED_SHOT_COLON_OUTSIDE_EMPHASIS = """
- **Test name**: test_rejects_empty_input
- **Behavior under test**: validate_scenario({}) raises ScenarioValidationError
- **Expected failure**: AssertionError: ScenarioValidationError not raised
- **Why this test first**: degenerate case — establishes the API contract
"""


class TestDegenerateCase(unittest.TestCase):
    """Empty signals — establishes return type and API contract."""

    def test_returns_list_for_empty_signals(self):
        result = check_mechanical("any output", EMPTY_SIGNALS)
        self.assertIsInstance(result, list)

    def test_returns_empty_list_for_empty_signals(self):
        result = check_mechanical("any output", EMPTY_SIGNALS)
        self.assertEqual(result, [])


class TestMustContain(unittest.TestCase):
    """must_contain checks — string must be present in output."""

    def test_must_contain_hit_passes(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["architecture"]}
        results = check_mechanical("We should analyse the architecture first.", signals)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)

    def test_must_contain_miss_fails(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["STOP condition"]}
        results = check_mechanical("Let us jump straight to a solution.", signals)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)

    def test_must_contain_multiple_all_present(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["existing", "pattern"]}
        results = check_mechanical("Follow the existing pattern in the codebase.", signals)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.passed for r in results))

    def test_must_contain_multiple_one_missing(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["existing", "STOP condition"]}
        results = check_mechanical("Follow the existing pattern in the codebase.", signals)
        self.assertEqual(len(results), 2)
        passed = [r.passed for r in results]
        self.assertIn(True, passed)
        self.assertIn(False, passed)

    def test_must_contain_matches_across_bold_emphasis(self):
        # "**Status**: Complete" — colon outside the bold. Cosmetic, and the
        # model gave the verdict, but raw matching scores it as non-compliant.
        signals = {**EMPTY_SIGNALS, "must_contain": ["Status:"]}
        results = check_mechanical("**Status**: Complete", signals)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)

    def test_must_contain_result_field_names_check(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["architecture"]}
        results = check_mechanical("Check the architecture.", signals)
        self.assertIn("architecture", results[0].field)


class TestMustNotContain(unittest.TestCase):
    """must_not_contain checks — string must be absent from output."""

    def test_must_not_contain_absent_passes(self):
        signals = {**EMPTY_SIGNALS, "must_not_contain": ["complete"]}
        results = check_mechanical("Implementation finished, moving to CHECK phase.", signals)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)

    def test_must_not_contain_present_fails(self):
        signals = {**EMPTY_SIGNALS, "must_not_contain": ["complete"]}
        results = check_mechanical("The implementation is complete.", signals)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)

    def test_must_not_contain_fires_across_bold_emphasis(self):
        # The CHECK template teaches the model to write "**Status:** Complete".
        # Raw substring matching does not see "Status: Complete" in that string,
        # so the guard against certifying unfinished work never fires.
        signals = {**EMPTY_SIGNALS, "must_not_contain": ["Status: Complete"]}
        results = check_mechanical("**Status:** Complete", signals)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)


class TestCalledShotRequired(unittest.TestCase):
    """called_shot_required checks — all four fields must be present in output."""

    def test_called_shot_not_required_produces_no_result(self):
        signals = {**EMPTY_SIGNALS, "called_shot_required": False}
        results = check_mechanical(CALLED_SHOT_FULL, signals)
        self.assertEqual(results, [])

    def test_called_shot_all_fields_present_passes(self):
        signals = {**EMPTY_SIGNALS, "called_shot_required": True}
        results = check_mechanical(CALLED_SHOT_FULL, signals)
        called_shot_results = [r for r in results if "called_shot" in r.field]
        self.assertEqual(len(called_shot_results), 1)
        self.assertTrue(called_shot_results[0].passed)

    def test_called_shot_missing_expected_failure_fails(self):
        signals = {**EMPTY_SIGNALS, "called_shot_required": True}
        results = check_mechanical(CALLED_SHOT_MISSING_EXPECTED_FAILURE, signals)
        called_shot_results = [r for r in results if "called_shot" in r.field]
        self.assertEqual(len(called_shot_results), 1)
        self.assertFalse(called_shot_results[0].passed)

    def test_called_shot_matches_across_bold_emphasis(self):
        # Observed live: 2-after-passing-test shot 3 failed on
        # "'Why this test first:' NOT found" while the GEval judge scored that
        # same response 0.90 and praised its called-shot discipline.
        signals = {**EMPTY_SIGNALS, "called_shot_required": True}
        results = check_mechanical(CALLED_SHOT_COLON_OUTSIDE_EMPHASIS, signals)
        called_shot_results = [r for r in results if "called_shot" in r.field]
        self.assertEqual(len(called_shot_results), 1)
        self.assertTrue(called_shot_results[0].passed)

    def test_called_shot_missing_all_fields_fails(self):
        signals = {**EMPTY_SIGNALS, "called_shot_required": True}
        results = check_mechanical("No called shot here at all.", signals)
        called_shot_results = [r for r in results if "called_shot" in r.field]
        self.assertEqual(len(called_shot_results), 1)
        self.assertFalse(called_shot_results[0].passed)


class TestNormalizationDoesNotOverreach(unittest.TestCase):
    """Guards that stripping `*` does not damage non-emphasis content.

    These were green before the normalization change and are green after —
    verified against the pre-change checker while recording the Step 0
    baseline. They are guards, not REDs: they pin the boundary of Decision #1
    (strip `*` only) so a later widening of _normalize cannot silently mangle
    code identifiers.
    """

    def test_underscored_identifiers_are_not_mangled(self):
        # `_` is code here, not emphasis. Stripping it would break this match.
        signals = {**EMPTY_SIGNALS, "must_not_contain": ["def deliver_webhook"]}
        results = check_mechanical("def deliver_webhook(payload):", signals)
        self.assertFalse(results[0].passed)

    def test_path_like_phrases_are_not_mangled(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["tests/test_http_headers.py"]}
        results = check_mechanical("Add it to tests/test_http_headers.py", signals)
        self.assertTrue(results[0].passed)

    def test_inline_code_phrases_still_match(self):
        signals = {**EMPTY_SIGNALS, "must_contain": ["bd update"]}
        results = check_mechanical("Run `bd update` before the GREEN phase.", signals)
        self.assertTrue(results[0].passed)

    def test_plain_text_is_unaffected(self):
        signals = {
            **EMPTY_SIGNALS,
            "must_contain": ["architecture"],
            "must_not_contain": ["shortcut"],
        }
        results = check_mechanical("Respect the existing architecture.", signals)
        self.assertTrue(all(r.passed for r in results))


if __name__ == "__main__":
    unittest.main(verbosity=2)
