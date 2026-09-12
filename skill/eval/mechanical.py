"""Mechanical (non-LLM) assertion checker for PDCA eval harness.

Checks observable string-level behaviors in LLM output:
- must_contain: required strings/phrases
- must_not_contain: forbidden strings/phrases
- called_shot_required: all four called-shot fields present
  (Test name, Behavior under test, Expected failure, Why this test first)
- verdict_fields_required / verdict_must_not_be: a verdict field's label and value in
  any rendering, not just the template's own literal line format
"""

import re
from dataclasses import dataclass

# Known verdict values per field label (#49/#111 loosening, second round). A
# same-time-window CI comparison measured 3-superpowers-verification-not-check drop
# from 6/8 to 1/8 passing shots after #49 added evidence-citation wording to the CHECK
# checklist -- not because the model's judgment got worse (GEval scored every one of
# those responses 0.90-1.00), but because responses shifted toward markdown-table
# formatting throughout, and the verdict section followed: "| **Status** | Needs work |"
# instead of "**Status:** Needs work". No colon appears anywhere in the table rendering,
# so a literal `must_contain: ["Status:"]` failed on a response a human would call
# correct. This mirrors #111's own already-applied fix for the same class of problem.
VERDICT_VALUES: dict[str, list[str]] = {
    "Status": ["Complete", "Needs work"],
    "Ready to close": ["Yes", "No"],
}

# Anything that isn't a letter/digit/underscore can separate a verdict label from its
# value: a colon-and-space ("Status: X"), a markdown table pipe ("Status | X"), a
# heading/table gap ("### Status\n\n| Status | X |"), or a status emoji the model
# inserted between them ("**Status:** ❌ Needs work"). \W already matches newlines
# and Unicode symbols, so both cross-line and emoji-separated renderings are covered.
_LABEL_TO_VALUE_GAP = r"\W{0,20}"


def _verdict_pattern(label: str, values: list[str]) -> re.Pattern[str]:
    # Case-insensitive on both label and value. Originally only the value was
    # case-folded, on the theory that a capitalized "Status" wouldn't collide with
    # incidental lowercase uses of the word elsewhere -- but a fresh CI re-validation
    # sample immediately produced two real, correct verdicts this missed: "Overall
    # status: Needs work" (lowercase label) and "Ready to Close: No" (title-cased
    # label). Capitalization is formatting on both sides, not a different field.
    value_alt = "|".join(re.escape(v) for v in values)
    return re.compile(r"(?i:" + re.escape(label) + _LABEL_TO_VALUE_GAP + value_alt + r")")


def _verdict_field_present(output: str, label: str) -> bool:
    values = VERDICT_VALUES[label]
    return _verdict_pattern(label, values).search(_normalize(output)) is not None


def _verdict_field_equals(output: str, label: str, forbidden_value: str) -> bool:
    """True if `label`'s stated verdict is `forbidden_value`, in any rendering."""
    pattern = _verdict_pattern(label, [forbidden_value])
    return pattern.search(_normalize(output)) is not None


def _normalize(text: str) -> str:
    """Strip markdown emphasis so signals match content, not formatting.

    Only `*` is removed. Underscores are left alone deliberately — the scenario
    suite contains phrases like `def deliver_webhook` and
    `tests/test_http_headers.py`, where an underscore is code rather than
    emphasis. Add further characters only when a real failure demands one.
    """
    return text.replace("*", "")


@dataclass
class CheckResult:
    field: str    # what was checked, e.g. "must_contain: 'pattern'"
    passed: bool  # True = check passed
    detail: str   # human-readable explanation


def check_mechanical(output: str, signals: dict) -> list[CheckResult]:
    """Run all mechanical checks against output. Returns list of CheckResult.

    Args:
        output: The LLM response string to check.
        signals: The expected_signals dict from a scenario, containing
                 must_contain, must_not_contain, called_shot_required.
    """
    results: list[CheckResult] = []

    for phrase in signals.get("must_contain", []):
        passed = _normalize(phrase) in _normalize(output)
        results.append(CheckResult(
            field=f"must_contain: '{phrase}'",
            passed=passed,
            detail=f"'{phrase}' {'found' if passed else 'NOT found'} in output",
        ))

    for phrase in signals.get("must_not_contain", []):
        passed = _normalize(phrase) not in _normalize(output)
        results.append(CheckResult(
            field=f"must_not_contain: '{phrase}'",
            passed=passed,
            detail=f"'{phrase}' {'absent (good)' if passed else 'FOUND (bad)'} in output",
        ))

    for label in signals.get("verdict_fields_required", []):
        passed = _verdict_field_present(output, label)
        results.append(CheckResult(
            field=f"verdict_fields_required: '{label}'",
            passed=passed,
            detail=f"'{label}' verdict {'found' if passed else 'NOT found'} in output (any rendering)",
        ))

    for label, forbidden_value in signals.get("verdict_must_not_be", {}).items():
        passed = not _verdict_field_equals(output, label, forbidden_value)
        results.append(CheckResult(
            field=f"verdict_must_not_be: '{label}' != '{forbidden_value}'",
            passed=passed,
            detail=(
                f"'{label}' is not '{forbidden_value}' (good)" if passed
                else f"'{label}' IS '{forbidden_value}' (bad)"
            ),
        ))

    if signals.get("called_shot_required", False):
        required_fields = [
            "Test name:",
            "Behavior under test:",
            "Expected failure:",
            "Why this test first:",
        ]
        normalized_output = _normalize(output)
        missing = [f for f in required_fields if _normalize(f) not in normalized_output]
        passed = len(missing) == 0
        results.append(CheckResult(
            field="called_shot: all four fields",
            passed=passed,
            detail=(
                "All four called-shot fields present"
                if passed
                else f"Missing: {missing}"
            ),
        ))

    return results
