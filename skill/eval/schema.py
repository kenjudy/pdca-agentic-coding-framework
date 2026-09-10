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
