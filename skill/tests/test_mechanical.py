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


class TestVerdictFieldsRequired(unittest.TestCase):
    """verdict_fields_required checks — a verdict field's label and value must appear
    together, in ANY rendering, not just the template's own literal line format (#49
    regression, second round of #111's loosening).

    A same-time-window CI comparison measured `3-superpowers-verification-not-check`
    drop from 6/8 to 1/8 passing shots after #49 added evidence-citation wording to the
    CHECK checklist (Fisher p ~= 0.041) -- not because the model's judgment got worse
    (GEval scored every one of those responses 0.90-1.00), but because responses shifted
    toward markdown-table formatting throughout, and the verdict section followed:
    "| **Status** | Needs work |" instead of "**Status:** Needs work". The literal
    substring "Status:" never appears in the table rendering -- there is no colon
    anywhere -- so `must_contain: ["Status:"]` failed on a response the judge, and a
    human reading it, would call correct.
    """

    def test_line_format_passes(self):
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("**Status:** Needs work", signals)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)

    def test_table_format_passes(self):
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("| **Status** | Needs work |", signals)
        self.assertTrue(results[0].passed)

    def test_heading_then_table_passes(self):
        """The exact shape captured from the real CI regression: a "### Status" heading
        with the actual value two rows into a table below it, no colon anywhere."""
        output = "### Status\n\n| | |\n|---|---|\n| **Status** | Needs work |"
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical(output, signals)
        self.assertTrue(results[0].passed)

    def test_ready_to_close_table_format_passes(self):
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Ready to close"]}
        results = check_mechanical("| **Ready to close** | No |", signals)
        self.assertTrue(results[0].passed)

    def test_missing_value_fails(self):
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("### Status\n\nSee above for details.", signals)
        self.assertFalse(results[0].passed)

    def test_label_absent_entirely_fails(self):
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("Everything looks fine.", signals)
        self.assertFalse(results[0].passed)

    def test_emoji_between_label_and_value_passes(self):
        """Real regression-run capture: replaying the actual CI outputs from the #49
        regression through an earlier version of this check found responses like this
        one failing -- the gap regex's character whitelist didn't include the checkmark
        emoji the model inserted between the colon and the value."""
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("**Status:** ❌ Needs work — two findings block close", signals)
        self.assertTrue(results[0].passed)

    def test_capitalized_value_passes(self):
        """Also found by replaying real captures: "### Status: ❌ Needs Work" (capital
        W) failed against a value list that only had "Needs work" (lowercase w) --
        capitalization is formatting, not a different verdict."""
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("### Status: ❌ Needs Work", signals)
        self.assertTrue(results[0].passed)

    def test_lowercase_label_passes(self):
        """Found from a fresh CI re-validation sample after the emoji/case-value fixes
        above: "Overall status: Needs work" (lowercase "status") failed against a label
        that only matched capital-S "Status". The label's case is formatting too --
        "status" and "Status" name the same field."""
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Status"]}
        results = check_mechanical("**Overall status: Needs work**", signals)
        self.assertTrue(results[0].passed)

    def test_title_case_label_passes(self):
        """Same CI sample, different field: "### Ready to Close: **No**" (capital C in
        Close) failed against the label "Ready to close" (lowercase c)."""
        signals = {**EMPTY_SIGNALS, "verdict_fields_required": ["Ready to close"]}
        results = check_mechanical("### Ready to Close: **No**", signals)
        self.assertTrue(results[0].passed)


class TestVerdictMustNotBe(unittest.TestCase):
    """verdict_must_not_be checks — a verdict field's stated value must not equal a
    forbidden one, in any rendering. Replaces `must_not_contain: ["Status: Complete"]`,
    which the same table-formatting shift would silently defeat the same way it broke
    verdict_fields_required's predecessor: "| Status | Complete |" contains no literal
    "Status: Complete" substring for the old guard to catch.
    """

    def test_line_format_forbidden_value_fails(self):
        signals = {**EMPTY_SIGNALS, "verdict_must_not_be": {"Status": "Complete"}}
        results = check_mechanical("**Status:** Complete", signals)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)

    def test_table_format_forbidden_value_fails(self):
        signals = {**EMPTY_SIGNALS, "verdict_must_not_be": {"Status": "Complete"}}
        results = check_mechanical("| **Status** | Complete |", signals)
        self.assertFalse(results[0].passed)

    def test_different_value_passes(self):
        signals = {**EMPTY_SIGNALS, "verdict_must_not_be": {"Status": "Complete"}}
        results = check_mechanical("| **Status** | Needs work |", signals)
        self.assertTrue(results[0].passed)

    def test_label_absent_entirely_passes(self):
        """No stated verdict at all is not the same failure this guard exists to
        catch -- verdict_fields_required is the check for that."""
        signals = {**EMPTY_SIGNALS, "verdict_must_not_be": {"Status": "Complete"}}
        results = check_mechanical("Everything looks fine.", signals)
        self.assertTrue(results[0].passed)


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
