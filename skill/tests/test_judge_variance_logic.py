"""Unit tests for the judge-variance probe's go/no-go decision rule (#190 Plan B).

Extracted from tests/test_judge_variance_190.py into eval/judge_variance.py so this
logic is unit-testable in the default suite without paying for the probe that produces
its inputs.

History of the rule itself, since it has already been wrong twice for opposite reasons:

1. Original inline rule (`anthropic_fail >= 1 and openai_fail <= 1`): a CHECK-phase
   critic pass traced it by hand and found it returned GO at 1-vs-1 failures -- no
   reduction at all. Nothing tested the rule, which is how that bug survived.
2. First fixed version (floor only, `anthropic_fail >= 2 and openai_fail < anthropic_fail`):
   a THIRD critic pass found this returned GO at 10-vs-0 and 10-vs-9 -- unanimous or
   near-unanimous Anthropic failure, which is uniform disagreement with the judge, not
   instability, and (given other findings from that same pass) the single most likely
   actual outcome of a real dispatch. The missing piece was an upper bound: real
   *instability* means a MIXED result, not "the judge always fails this."
"""

from eval.judge_variance import decide_go


class TestDecideGo:

    def test_no_go_at_equal_failure_counts(self):
        """The original bug: 1-vs-1 is zero reduction, not a passing signal."""
        assert decide_go(anthropic_fail=1, openai_fail=1) is False

    def test_go_when_anthropic_unstable_and_openai_clean(self):
        assert decide_go(anthropic_fail=3, openai_fail=0) is True

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

    def test_no_go_at_unanimous_anthropic_failure(self):
        """The exact regression a third critic pass found: 10/10 Anthropic failures is
        consistent disagreement with the judge, not instability -- and, combined with a
        canary that (at the time) still had real compliance problems and a temperature
        pinning that removed Anthropic's own production variance, was the single most
        likely actual outcome of a real dispatch. GO here would have been read as
        'OpenAI fixes instability' when the true story was 'the canary is bad.'"""
        assert decide_go(anthropic_fail=10, openai_fail=0) is False

    def test_no_go_above_the_instability_ceiling(self):
        """9/10 is still near-unanimous, not mixed."""
        assert decide_go(anthropic_fail=9, openai_fail=0) is False

    def test_go_at_the_ceiling_boundary(self):
        """With the default n_shots=10 and the floor at 2, the symmetric ceiling is 8."""
        assert decide_go(anthropic_fail=8, openai_fail=0) is True

    def test_no_go_when_openai_exceeds_the_cap(self):
        """The original rule's `openai_fail <= 1` cap was dropped when the floor was
        added, which is what let 10-vs-9 read as GO. Restored here, independent of the
        floor/ceiling: an OpenAI arm failing 2+ times is not a clean result regardless of
        how unstable the Anthropic arm is."""
        assert decide_go(anthropic_fail=5, openai_fail=2) is False

    def test_respects_a_custom_n_shots(self):
        """The floor/ceiling symmetry must scale with n_shots, not assume 10 -- the
        probe's own N_SHOTS_PER_ARM could change independently of this rule."""
        assert decide_go(anthropic_fail=2, openai_fail=0, n_shots=4) is True
        assert decide_go(anthropic_fail=3, openai_fail=0, n_shots=4) is False
