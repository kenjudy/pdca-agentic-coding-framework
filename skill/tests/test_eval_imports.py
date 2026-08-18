"""Smoke test for the eval harness's third-party surface (issue #122).

The unit suite never touches `anthropic` or `deepeval`: `eval/executor.py` imports
anthropic lazily inside a function body, and `tests/test_evals.py` is excluded from
the default run. So a dependency upgrade could break the harness completely and every
test would still pass -- which is exactly what happened when the lockfile was
refreshed across `deepeval` 3.9.9 -> 4.1.8, a major version.

This file mirrors the imports and constructions `tests/test_evals.py` performs, so a
signature or module move in either package fails here instead of surfacing mid-cycle
the next time someone tries to validate a prompt change.

**No API calls.** `AnthropicModel` requires a key at construction time in deepeval 4.x,
so a clearly-fake one is passed. Nothing here reaches the network, and this file must
stay that way -- the moment it needs a real key it stops being runnable in CI and
becomes another gate that quietly does not run.

Excluded from the default suite (see `addopts` in pyproject.toml) because it needs the
`eval` extra, which the project installs separately. The `eval-imports` job in
.github/workflows/test.yml syncs that extra and runs this file. It is deliberately not
guarded by a skip: a skipped smoke test is indistinguishable from a passing one.
"""

import unittest

from deepeval.metrics import GEval
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# Matches tests/test_evals.py's JUDGE_MODEL. Kept in sync deliberately: the point is to
# exercise the same construction the real harness performs.
JUDGE_MODEL_NAME = "claude-haiku-4-5-20251001"

# Obviously fake, and never used against the network -- construction only.
DUMMY_API_KEY = "sk-ant-dummy-key-for-construction-only"


class TestEvalHarnessImports(unittest.TestCase):
    """Every symbol tests/test_evals.py imports must still exist and construct."""

    def test_anthropic_client_class_is_importable(self):
        """eval/executor.py does `import anthropic` then `anthropic.Anthropic()`."""
        import anthropic

        self.assertTrue(
            hasattr(anthropic, "Anthropic"),
            "anthropic.Anthropic is gone -- eval/executor.py's client construction is broken",
        )

    def test_judge_model_constructs(self):
        """tests/test_evals.py builds this at module import time, so a signature change
        there breaks collection of the entire eval suite, not just one test."""
        model = AnthropicModel(model=JUDGE_MODEL_NAME, api_key=DUMMY_API_KEY)
        self.assertIsNotNone(model)

    def test_geval_metric_constructs(self):
        """GEval is the scoring surface the rubrics are written against."""
        metric = GEval(
            name="smoke",
            criteria="A placeholder criterion used only to construct the metric.",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
            model=AnthropicModel(model=JUDGE_MODEL_NAME, api_key=DUMMY_API_KEY),
        )
        self.assertEqual(metric.name, "smoke")

    def test_llm_test_case_carries_input_and_output(self):
        case = LLMTestCase(input="a prompt", actual_output="a response")
        self.assertEqual(case.input, "a prompt")
        self.assertEqual(case.actual_output, "a response")

    def test_rubrics_import_against_the_installed_deepeval(self):
        """The rubric modules are the project's own code built on deepeval's API.

        Importing them here catches the case where deepeval still provides everything
        above but the rubrics use something it moved.
        """
        from eval.rubrics import rubric_1a  # noqa: F401

        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
