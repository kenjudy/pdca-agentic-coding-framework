"""Mechanical (non-LLM) assertion checker for PDCA eval harness.

Checks observable string-level behaviors in LLM output:
- must_contain: required strings/phrases
- must_not_contain: forbidden strings/phrases
- called_shot_required: all four called-shot fields present
  (Test name, Behavior under test, Expected failure, Why this test first)
"""

from dataclasses import dataclass


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
