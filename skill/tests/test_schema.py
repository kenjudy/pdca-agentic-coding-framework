"""Tests for eval scenario schema validation."""

import unittest

from eval.schema import ScenarioValidationError, validate_scenario

VALID_SCENARIO = {
    "prompt_id": "1a",
    "scenario_id": "1a_clear_goal",
    "description": "User has a clear coding goal with an existing codebase",
    "input": "I need to add OAuth2 authentication to our Express.js API.",
    "expected_signals": {
        "must_contain": ["existing", "pattern"],
        "must_not_contain": ["complete"],
        "called_shot_required": False,
    },
}


class TestSchemaRejectsInvalid(unittest.TestCase):
    """Degenerate and invalid cases — validator must raise ScenarioValidationError."""

    def test_rejects_empty_dict(self):
        with self.assertRaises(ScenarioValidationError):
            validate_scenario({})

    def test_rejects_missing_prompt_id(self):
        scenario = {**VALID_SCENARIO}
        del scenario["prompt_id"]
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)

    def test_rejects_missing_input(self):
        scenario = {**VALID_SCENARIO}
        del scenario["input"]
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)

    def test_rejects_missing_expected_signals(self):
        scenario = {**VALID_SCENARIO}
        del scenario["expected_signals"]
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)

    def test_rejects_missing_must_contain(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {**VALID_SCENARIO["expected_signals"]}}  # type: ignore[dict-item]
        del scenario["expected_signals"]["must_contain"]  # type: ignore[attr-defined]
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)

    def test_rejects_missing_called_shot_required(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {**VALID_SCENARIO["expected_signals"]}}  # type: ignore[dict-item]
        del scenario["expected_signals"]["called_shot_required"]  # type: ignore[attr-defined]
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)

    def test_rejects_must_contain_not_a_list(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {
            **VALID_SCENARIO["expected_signals"],  # type: ignore[dict-item]
            "must_contain": "not-a-list",
        }}
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)

    def test_rejects_called_shot_required_not_a_bool(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {
            **VALID_SCENARIO["expected_signals"],  # type: ignore[dict-item]
            "called_shot_required": "yes",
        }}
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)


class TestSchemaAcceptsValid(unittest.TestCase):
    """Happy path — valid scenarios must pass without error."""

    def test_accepts_valid_scenario(self):
        validate_scenario(VALID_SCENARIO)  # must not raise

    def test_accepts_empty_signal_lists(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {
            "must_contain": [],
            "must_not_contain": [],
            "called_shot_required": False,
        }}
        validate_scenario(scenario)  # must not raise

    def test_accepts_called_shot_required_true(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {
            **VALID_SCENARIO["expected_signals"],  # type: ignore[dict-item]
            "called_shot_required": True,
        }}
        validate_scenario(scenario)  # must not raise

    def test_accepts_skip_geval_true(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {
            **VALID_SCENARIO["expected_signals"],  # type: ignore[dict-item]
            "skip_geval": True,
        }}
        validate_scenario(scenario)  # must not raise

    def test_rejects_skip_geval_not_bool(self):
        scenario = {**VALID_SCENARIO, "expected_signals": {
            **VALID_SCENARIO["expected_signals"],  # type: ignore[dict-item]
            "skip_geval": "yes",
        }}
        with self.assertRaises(ScenarioValidationError):
            validate_scenario(scenario)


if __name__ == "__main__":
    unittest.main(verbosity=2)
