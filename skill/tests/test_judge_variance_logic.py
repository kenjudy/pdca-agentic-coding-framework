"""Unit tests for the judge-variance probe's go/no-go decision rule (#190 Plan B).

Extracted from tests/test_judge_variance_190.py into eval/judge_variance.py so this
logic is unit-testable in the default suite without paying for the probe that produces
its inputs. A CHECK-phase critic pass traced the original inline rule
(`anthropic_fail >= 1 and openai_fail <= 1`) by hand and found it returned GO at 1-vs-1
failures -- no reduction at all -- contradicting its own stated intent of "a visible
reduction in false-fail rate ... not a coin flip". Nothing tested the rule itself, which
is how that bug survived.
"""

from eval.judge_variance import decide_go


class TestDecideGo:

    def test_no_go_at_equal_failure_counts(self):
        """The exact bug: 1-vs-1 is zero reduction, not a passing signal."""
        assert decide_go(anthropic_fail=1, openai_fail=1) is False

    def test_go_when_anthropic_unstable_and_openai_clean(self):
        assert decide_go(anthropic_fail=3, openai_fail=0) is True

    def test_no_go_when_openai_fails_more_than_anthropic(self):
        assert decide_go(anthropic_fail=1, openai_fail=2) is False

    def test_no_go_when_anthropic_failure_count_is_below_the_instability_floor(self):
        """A single Anthropic failure could be noise -- CHANGELOG.md already records an
        underpowered n=6/arm Haiku-vs-Opus A/B (Fisher p=1.0 and p=0.455) from earlier in
        this same investigation. Requiring only >=1 failure treats one fluke as proof of
        instability."""
        assert decide_go(anthropic_fail=1, openai_fail=0) is False

    def test_go_at_the_instability_floor_boundary(self):
        assert decide_go(anthropic_fail=2, openai_fail=1) is True

    def test_no_go_when_openai_matches_anthropics_instability(self):
        assert decide_go(anthropic_fail=5, openai_fail=5) is False
