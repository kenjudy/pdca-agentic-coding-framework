"""Unit tests for eval.judges — no API calls, no deepeval import at collection time.

Provider selection and name resolution are pure and belong in the default suite.
Actual client construction (which needs deepeval) is tested keylessly in
tests/test_eval_imports.py instead — see that file for why.
"""

from eval.judges import (
    ANTHROPIC_JUDGE_MODEL_NAME,
    OPENAI_JUDGE_MODEL_NAME,
    UnknownJudgeProvider,
    judge_provider_from_env,
    resolve_judge_model_name,
)


class TestJudgeProviderFromEnv:

    def test_defaults_to_anthropic_when_unset(self):
        assert judge_provider_from_env({}) == "anthropic"

    def test_returns_openai_when_set(self):
        assert judge_provider_from_env({"PDCA_EVAL_JUDGE": "openai"}) == "openai"

    def test_returns_anthropic_when_explicitly_set(self):
        assert judge_provider_from_env({"PDCA_EVAL_JUDGE": "anthropic"}) == "anthropic"

    def test_raises_on_unknown_provider(self):
        try:
            judge_provider_from_env({"PDCA_EVAL_JUDGE": "gpt4"})
            assert False, "expected UnknownJudgeProvider"
        except UnknownJudgeProvider:
            pass

    def test_ignores_unrelated_env_vars(self):
        assert judge_provider_from_env({"PATH": "/usr/bin", "HOME": "/root"}) == "anthropic"


class TestResolveJudgeModelName:

    def test_anthropic_name(self):
        assert resolve_judge_model_name("anthropic") == ANTHROPIC_JUDGE_MODEL_NAME

    def test_openai_name(self):
        assert resolve_judge_model_name("openai") == OPENAI_JUDGE_MODEL_NAME

    def test_raises_on_unknown_provider(self):
        try:
            resolve_judge_model_name("gpt4")
            assert False, "expected UnknownJudgeProvider"
        except UnknownJudgeProvider:
            pass

    def test_does_not_require_deepeval(self):
        """Name resolution must work even where deepeval is not installed -- this is
        the whole reason it exists as a function separate from the builders. This test
        runs in the default suite, which never installs deepeval; if resolving a name
        required constructing a client, this test itself would fail to import."""
        assert resolve_judge_model_name("anthropic") == "claude-haiku-4-5-20251001"
