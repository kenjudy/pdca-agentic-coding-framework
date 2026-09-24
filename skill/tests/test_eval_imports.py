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
from unittest import mock

from deepeval.metrics import GEval
from deepeval.metrics.g_eval.utils import no_log_prob_support
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.judges import OPENAI_JUDGE_MODEL_NAME, anthropic_judge_model, openai_judge_model

# tests/test_evals.py resolves its judge through eval.judges too (#190 Plan B), so this
# mirrors the same construction the real harness performs via the same source of truth.
JUDGE_MODEL_NAME = "claude-haiku-4-5-20251001"

# Obviously fake, and never used against the network -- construction only.
DUMMY_API_KEY = "sk-ant-dummy-key-for-construction-only"
DUMMY_OPENAI_API_KEY = "sk-dummy-key-for-construction-only"


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
        """tests/test_evals.py's judge_model() builds this lazily on first use (#156);
        a signature change here breaks the whole eval suite's judging, not just one
        test, so it is checked keylessly rather than only discovered by paying for a
        run."""
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

    def test_openai_judge_model_constructs(self):
        """eval.judges.openai_judge_model(), built lazily the same way
        anthropic_judge_model() is. Needs a key at construction time in this deepeval
        version -- confirmed directly, contrary to an earlier assumption that
        construction was keyless; OpenAIModel's __init__ calls load_model()
        immediately, same as AnthropicModel."""
        with mock.patch.dict("os.environ", {"OPENAI_API_KEY": DUMMY_OPENAI_API_KEY}):
            model = openai_judge_model()
        self.assertIsNotNone(model)

    def test_anthropic_judge_model_constructs_via_eval_judges(self):
        """The extracted builder (#190 Plan B step 1) must still construct the same
        client tests/test_evals.py's judge_model() used to build directly."""
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": DUMMY_API_KEY}):
            model = anthropic_judge_model()
        self.assertIsNotNone(model)

    def test_openai_judge_supports_log_probs(self):
        """Guards the mechanism #190 Plan B exists to test (#190 Plan B step 4).

        deepeval's GEval is logprob-weighted-sum scoring for models it recognizes as
        capable; AnthropicModel falls back to a single unweighted sample because it
        lacks generate_raw_response entirely. Swapping OPENAI_JUDGE_MODEL_NAME to a
        model without logprob support -- confirmed here to be the common case, not the
        exception: every GPT-5.x mini/nano variant in deepeval's own registry has
        supports_log_probs=False -- would silently revert to the same unweighted path
        while still producing a normal-looking report. Two checks, because
        no_log_prob_support() alone does not discriminate this: it returns False for
        ANY model type it does not specifically recognize (confirmed by reading its
        source -- it only inspects str/OpenAIModel/AzureOpenAIModel), so it returns
        False for AnthropicModel too, despite Anthropic not actually supporting the
        weighted path. The second check (generate_raw_response) is what actually
        distinguishes the two providers.

        Deliberately does NOT assert `model_data.max_log_probs is not None` -- verified
        directly that gpt-4o-mini's max_log_probs is None despite supports_log_probs
        being True, so that assertion would fail on the very model this guards.

        Built via `openai_judge_model()` -- the real production builder, using the real
        `OPENAI_JUDGE_MODEL_NAME` constant -- not a hand-rolled `OpenAIModel(...)` call
        with a locally duplicated model-name literal. A CHECK-phase critic pass found
        the earlier version of this test built its own `OpenAIModel` from a copy of the
        constant declared in this file, so swapping the real `eval.judges.
        OPENAI_JUDGE_MODEL_NAME` to a model without logprob support (verified: this
        test still passed with it set to "gpt-5.4-mini") went completely undetected --
        the opposite of what this test claims to guard.
        """
        with mock.patch.dict("os.environ", {"OPENAI_API_KEY": DUMMY_OPENAI_API_KEY}):
            model = openai_judge_model()
        self.assertFalse(
            no_log_prob_support(model),
            f"{OPENAI_JUDGE_MODEL_NAME} no longer supports logprob-weighted scoring "
            "per deepeval's model registry -- the judge swap would silently revert to "
            "unweighted single-sample scoring, the exact defect this test exists to catch",
        )
        self.assertTrue(
            hasattr(model, "generate_raw_response"),
            "OpenAIModel lost generate_raw_response -- GEval's weighted-scoring path "
            "calls this method; its absence is what makes AnthropicModel fall back to "
            "unweighted scoring, and losing it here would do the same silently",
        )


if __name__ == "__main__":
    unittest.main()
