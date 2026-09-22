"""GEval judge-model selection and construction (#190 Plan B).

Extracted from tests/test_evals.py's `judge_model()` (#156's deferred-construction
pattern) so the builders are importable and testable without the `eval` extra or a live
key -- tests/test_evals.py is excluded from the default suite (pyproject.toml addopts)
and can only be exercised by paying for a run. tests/test_eval_imports.py is where a
construction can be checked for free, with a dummy key, and this module is its home.

Each builder is cached per provider (not a single module-level judge) so that resolving
a different provider mid-session -- e.g. two tests in the same process asking for
different PDCA_EVAL_JUDGE values -- cannot silently return the wrong cached client.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deepeval.models.base_model import DeepEvalBaseLLM

ANTHROPIC_JUDGE_MODEL_NAME = "claude-haiku-4-5-20251001"
# gpt-4o-mini, not the newer/cheaper gpt-5.4-mini or gpt-4.1-mini: deepeval's own model
# registry (models/llms/constants.py) shows every GPT-5.x mini/nano variant with
# supports_log_probs=False -- only full-size gpt-5.4 keeps it in that generation -- and
# gpt-4.1-mini already has an announced OpenAI API cutoff (2026-10-14). gpt-4o-mini is
# the cheapest currently-available model that still exercises the logprob-weighted path
# this investigation is testing, with no announced API-level retirement date as of
# writing. It has no committed lifespan either: if OpenAI deprecates it, the guard test
# below (test_eval_imports.py) is the tripwire -- swapping to whatever replaces it
# without re-checking supports_log_probs will very likely fail that test outright, given
# every other newer/smaller OpenAI model observed here has dropped the capability.
OPENAI_JUDGE_MODEL_NAME = "gpt-4o-mini"

_ANTHROPIC = "anthropic"
_OPENAI = "openai"
_PROVIDERS = (_ANTHROPIC, _OPENAI)


class UnknownJudgeProvider(KeyError):
    """PDCA_EVAL_JUDGE (or an explicit provider argument) named something this module
    does not build a judge for.

    Raised rather than silently falling back to the default -- a typo that resolved to
    "use Haiku anyway" would produce a normal-looking report while testing a different
    hypothesis than the one requested.
    """


_judge_models: dict[str, DeepEvalBaseLLM] = {}


def judge_provider_from_env(env: Mapping[str, str]) -> str:
    """Which judge provider to use, from PDCA_EVAL_JUDGE. Defaults to 'anthropic' --
    every existing eval run before this option existed used Haiku, so an unset variable
    must reproduce that behavior exactly."""
    provider = env.get("PDCA_EVAL_JUDGE", _ANTHROPIC)
    if provider not in _PROVIDERS:
        raise UnknownJudgeProvider(
            f"PDCA_EVAL_JUDGE={provider!r} is not a known judge provider; "
            f"expected one of {_PROVIDERS}"
        )
    return provider


def resolve_judge_model_name(provider: str) -> str:
    """The model name string for a provider, without constructing a client.

    EvalReporter's provenance field (#190 Plan B step 0) needs this name at fixture
    setup, which may run before any judge call actually happens -- resolving it via the
    builder would force construction (and therefore a key) earlier than necessary.
    """
    if provider == _ANTHROPIC:
        return ANTHROPIC_JUDGE_MODEL_NAME
    if provider == _OPENAI:
        return OPENAI_JUDGE_MODEL_NAME
    raise UnknownJudgeProvider(
        f"provider={provider!r} is not a known judge provider; expected one of {_PROVIDERS}"
    )


def anthropic_judge_model() -> DeepEvalBaseLLM:
    """The Anthropic (Haiku) GEval judge, built on first use rather than at import
    (#156). deepeval raises during AnthropicModel construction when no key is
    configured, so building this eagerly would make the module unimportable without a
    credential."""
    if _ANTHROPIC not in _judge_models:
        from deepeval.models import AnthropicModel  # type: ignore[import-untyped]

        _judge_models[_ANTHROPIC] = AnthropicModel(model=ANTHROPIC_JUDGE_MODEL_NAME)
    return _judge_models[_ANTHROPIC]


def openai_judge_model() -> DeepEvalBaseLLM:
    """The OpenAI (gpt-4o-mini) GEval judge, built on first use for the same reason as
    anthropic_judge_model()."""
    if _OPENAI not in _judge_models:
        from deepeval.models import OpenAIModel  # type: ignore[import-untyped]

        _judge_models[_OPENAI] = OpenAIModel(model=OPENAI_JUDGE_MODEL_NAME)
    return _judge_models[_OPENAI]


def judge_model(provider: str) -> DeepEvalBaseLLM:
    """The judge client for an already-resolved provider name."""
    if provider == _ANTHROPIC:
        return anthropic_judge_model()
    if provider == _OPENAI:
        return openai_judge_model()
    raise UnknownJudgeProvider(
        f"provider={provider!r} is not a known judge provider; expected one of {_PROVIDERS}"
    )
