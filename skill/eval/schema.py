"""Scenario schema validation for PDCA eval harness."""


class ScenarioValidationError(ValueError):
    pass


def validate_scenario(scenario: dict) -> None:
    """Validate a scenario dict against the required schema.

    Required top-level fields: prompt_id, scenario_id, description, input, expected_signals
    Required expected_signals fields: must_contain (list), must_not_contain (list),
                                      called_shot_required (bool)

    Raises ScenarioValidationError if the scenario is invalid.
    """
    required_top = ["prompt_id", "scenario_id", "description", "input", "expected_signals"]
    for field in required_top:
        if field not in scenario:
            raise ScenarioValidationError(f"Missing required field: '{field}'")

    signals = scenario["expected_signals"]
    required_signals = ["must_contain", "must_not_contain", "called_shot_required"]
    for field in required_signals:
        if field not in signals:
            raise ScenarioValidationError(f"Missing required field in expected_signals: '{field}'")

    if not isinstance(signals["must_contain"], list):
        raise ScenarioValidationError("expected_signals.must_contain must be a list")
    if not isinstance(signals["must_not_contain"], list):
        raise ScenarioValidationError("expected_signals.must_not_contain must be a list")
    if not isinstance(signals["called_shot_required"], bool):
        raise ScenarioValidationError("expected_signals.called_shot_required must be a bool")

    if "skip_geval" in signals and not isinstance(signals["skip_geval"], bool):
        raise ScenarioValidationError("expected_signals.skip_geval must be a bool")

    _validate_geval_criteria(signals)


def _validate_geval_criteria(signals: dict) -> None:
    """Validate optional per-scenario criteria scoping (#148).

    Absent means the scenario is judged against its whole phase rubric, which is what
    every scenario did before scoping existed.

    Narrowing must be argued rather than merely declared. Without the reason requirement,
    `geval_criteria` is a nicer-looking `skip_geval`: a way to make a red scenario green by
    quietly dropping the criterion it fails, indistinguishable in the report from a
    scenario that passed on merit.
    """
    if "geval_criteria" not in signals:
        return

    criteria = signals["geval_criteria"]
    if not isinstance(criteria, list):
        raise ScenarioValidationError("expected_signals.geval_criteria must be a list")
    if not criteria:
        raise ScenarioValidationError(
            "expected_signals.geval_criteria must not be empty -- an empty selection is "
            "skip_geval with extra steps, and bypasses the invariant that a skip_geval "
            "scenario still asserts something mechanically"
        )
    for item in criteria:
        if not isinstance(item, str):
            raise ScenarioValidationError(
                f"expected_signals.geval_criteria entries must be strings, got {item!r}"
            )

    reason = signals.get("geval_criteria_reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ScenarioValidationError(
            "expected_signals.geval_criteria_reason is required when geval_criteria "
            "narrows the rubric, and must say why the omitted criteria do not apply to "
            "what this scenario claims to measure"
        )
