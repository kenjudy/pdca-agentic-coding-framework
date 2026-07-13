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

    def test_called_shot_missing_all_fields_fails(self):
        signals = {**EMPTY_SIGNALS, "called_shot_required": True}
        results = check_mechanical("No called shot here at all.", signals)
        called_shot_results = [r for r in results if "called_shot" in r.field]
        self.assertEqual(len(called_shot_results), 1)
        self.assertFalse(called_shot_results[0].passed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
