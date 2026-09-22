"""Pure decision-rule logic for the judge-variance probe (#190 Plan B).

Extracted from tests/test_judge_variance_190.py so the go/no-go rule is unit-testable
in the default suite without paying for the probe that produces its inputs -- see
tests/test_judge_variance_logic.py, which also records this rule's history: it has
already been wrong twice, for opposite reasons (no floor, then no ceiling).
"""

from __future__ import annotations

# Below this many Anthropic-arm failures, a "reduction" could be a single fluke rather
# than real instability -- CHANGELOG.md already records an underpowered n=6/arm
# Haiku-vs-Opus A/B (Fisher p=1.0 and p=0.455) from earlier in this same investigation.
# Symmetric with the ceiling below: real *instability* means a MIXED result, and a
# result this close to either extreme (0 or n_shots) isn't mixed, whichever end it's on.
MIN_ANTHROPIC_FAILURES_FOR_SIGNAL = 2

# Above this many OpenAI-arm failures, the result isn't clean regardless of how
# unstable the Anthropic arm is -- restored after a third critic pass found the
# floor-only version of this rule returned GO at 10-vs-9 (OpenAI failing 9 of 10 shots
# on the same "known-compliant" canary), which really means the canary is bad, not that
# OpenAI is the more stable judge.
MAX_OPENAI_FAILURES_FOR_SIGNAL = 1


def decide_go(anthropic_fail: int, openai_fail: int, n_shots: int = 10) -> bool:
    """Whether the probe's result supports proceeding to the CI/docs steps gated on it.

    Three requirements, all independent of each other by design (a mutation removing
    any one of them should fail a test in tests/test_judge_variance_logic.py):

    1. The Anthropic arm's failure count is MIXED -- between the floor and a symmetric
       ceiling (n_shots - floor) -- not near either extreme. Unanimous or
       near-unanimous failure (e.g. 10/10 or 9/10) is uniform disagreement with the
       judge, not instability; a single failure could be noise.
    2. The OpenAI arm's failure count stays at or below a small cap, independent of the
       Anthropic arm's count.
    3. The OpenAI arm fails strictly fewer times than the Anthropic arm.
    """
    ceiling = n_shots - MIN_ANTHROPIC_FAILURES_FOR_SIGNAL
    mixed_anthropic_result = MIN_ANTHROPIC_FAILURES_FOR_SIGNAL <= anthropic_fail <= ceiling
    openai_capped = openai_fail <= MAX_OPENAI_FAILURES_FOR_SIGNAL
    strict_improvement = openai_fail < anthropic_fail
    return mixed_anthropic_result and openai_capped and strict_improvement
