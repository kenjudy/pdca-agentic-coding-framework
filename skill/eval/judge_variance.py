"""Pure decision-rule logic for the judge-variance probe (#190 Plan B).

Extracted from tests/test_judge_variance_190.py so the go/no-go rule is unit-testable
in the default suite without paying for the probe that produces its inputs -- see
tests/test_judge_variance_logic.py.
"""

from __future__ import annotations

# Below this many Anthropic-arm failures, a "reduction" could be a single fluke rather
# than real instability -- CHANGELOG.md already records an underpowered n=6/arm
# Haiku-vs-Opus A/B (Fisher p=1.0 and p=0.455) from earlier in this same investigation.
MIN_ANTHROPIC_FAILURES_FOR_SIGNAL = 2


def decide_go(anthropic_fail: int, openai_fail: int) -> bool:
    """Whether the probe's result supports proceeding to the CI/docs steps gated on it.

    Requires the Anthropic arm to show real instability (not a single fluke) AND the
    OpenAI arm to show a STRICTLY lower failure count than Anthropic -- not merely a
    tie or a worse result. The original inline version of this rule
    (`anthropic_fail >= 1 and openai_fail <= 1`) allowed both silently: a CHECK-phase
    critic pass traced it by hand and found it returned GO at 1-vs-1 (zero reduction)
    and at 1-vs-0 (where Fisher exact gives p=1.0, i.e. indistinguishable from noise).
    """
    meaningful_anthropic_instability = anthropic_fail >= MIN_ANTHROPIC_FAILURES_FOR_SIGNAL
    strict_improvement = openai_fail < anthropic_fail
    return meaningful_anthropic_instability and strict_improvement
