"""Unit tests for eval.aggregate — pooling verdicts across runs (#147 deliverable 2)."""

import textwrap

import pytest

from eval.aggregate import aggregate_reports, format_summary, parse_report


def _report(rows, details=""):
    """A minimal report in EvalReporter's rendered shape."""
    head = textwrap.dedent("""\
        # PDCA Eval Report — 2026-09-10 12:00:00

        **Environment:** deepeval: 4.2.2, anthropic: 1.4.0

        ## Summary

        | Scenario | Phase | Score | Threshold | GEval | Mechanical |
        |----------|-------|-------|-----------|-------|------------|
        """)
    return head + "\n".join(rows) + "\n\n## Scenario Details\n" + details


class TestParseReport:
    def test_reads_verdicts_and_score_from_the_summary(self):
        parsed = parse_report(_report(["| 2-first-step | TDD | 0.70 | 0.50 | ✅ | ✅ |"]))
        run = parsed["2-first-step"]
        assert run.geval_passed is True
        assert run.mechanical_passed is True
        assert run.scores == [0.70]

    def test_reads_individual_shots_when_a_scenario_was_retried(self):
        """A retried row shows 'mean ± stddev', which is not a score anyone observed. The
        shots are the measurements and the distribution has to be built from them."""
        details = textwrap.dedent("""\
            ### 4-short-session (Retrospection)

            **Shot 1:** GEval 0.20 ❌ | Mechanical ✅
            **Shot 2:** GEval 0.90 ✅ | Mechanical ✅
            **Shot 3:** GEval 0.60 ✅ | Mechanical ✅
            """)
        parsed = parse_report(
            _report(["| 4-short-session | Retrospection | 0.5667 ± 0.3215 | 0.50 | ✅ | ✅ |"], details)
        )
        assert parsed["4-short-session"].scores == [0.20, 0.90, 0.60]

    def test_skipped_geval_contributes_no_score(self):
        """skip_geval renders 'n/a'. Treating that as 0.0 would invent a measurement."""
        parsed = parse_report(
            _report(["| 2-skip-tests-request | TDD | n/a | 0.00 | ✅ | ✅ |"])
        )
        assert parsed["2-skip-tests-request"].scores == []


class TestAggregate:
    def test_verdict_is_stable_when_every_run_agrees(self):
        reports = [_report(["| s | TDD | 0.90 | 0.50 | ✅ | ✅ |"]) for _ in range(3)]
        agg = aggregate_reports(reports)["s"]
        assert agg.runs == 3
        assert agg.verdict_unstable is False

    def test_verdict_is_unstable_when_a_scenario_both_passed_and_failed(self):
        """The actionable fact, and not an inference: a scenario that changes verdict
        across runs cannot serve as a regression gate, whatever the cause. #111 and #136
        are both instances, and both took a human reading responses to establish."""
        reports = [
            _report(["| s | TDD | 0.90 | 0.50 | ✅ | ✅ |"]),
            _report(["| s | TDD | 0.30 | 0.50 | ❌ | ✅ |"]),
        ]
        agg = aggregate_reports(reports)["s"]
        assert agg.verdict_unstable is True

    def test_counts_runs_where_the_two_tiers_disagreed(self):
        reports = [
            _report(["| s | TDD | 0.30 | 0.50 | ❌ | ✅ |"]),
            _report(["| s | TDD | 0.90 | 0.50 | ✅ | ✅ |"]),
        ]
        assert aggregate_reports(reports)["s"].divergent_runs == 1

    def test_pools_scores_across_reports(self):
        reports = [
            _report(["| s | TDD | 0.90 | 0.50 | ✅ | ✅ |"]),
            _report(["| s | TDD | 0.30 | 0.50 | ❌ | ✅ |"]),
        ]
        assert sorted(aggregate_reports(reports)["s"].scores) == [0.30, 0.90]


class TestFormatSummary:
    def test_names_unstable_scenarios(self):
        reports = [
            _report(["| flaky | TDD | 0.90 | 0.50 | ✅ | ✅ |"]),
            _report(["| flaky | TDD | 0.30 | 0.50 | ❌ | ✅ |"]),
        ]
        out = format_summary(aggregate_reports(reports))
        assert "flaky" in out
        assert "1 pass / 1 fail" in out

    def test_does_not_attribute_a_cause(self):
        """#147, corrected: the band ladder produces a gap at the threshold structurally
        (#153), so a shape alone cannot distinguish an unstable judge from an unstable
        model. Reporting either as a conclusion would be #141's defect one level up --
        output that reads like a measurement."""
        reports = [
            _report(["| flaky | TDD | 0.90 | 0.50 | ✅ | ✅ |"]),
            _report(["| flaky | TDD | 0.30 | 0.50 | ❌ | ✅ |"]),
        ]
        out = format_summary(aggregate_reports(reports)).lower()
        for verdict_word in ("judge instability", "rubric fault", "model is flaky"):
            assert verdict_word not in out

    def test_reports_nothing_to_flag_when_everything_is_stable(self):
        reports = [_report(["| s | TDD | 0.90 | 0.50 | ✅ | ✅ |"]) for _ in range(3)]
        assert "no scenario changed verdict" in format_summary(aggregate_reports(reports)).lower()

    def test_requires_more_than_one_report(self):
        """One run cannot show instability, and saying 'stable' from a single observation
        is exactly the claim CLAUDE.md warns against."""
        with pytest.raises(ValueError):
            aggregate_reports([_report(["| s | TDD | 0.90 | 0.50 | ✅ | ✅ |"])])
