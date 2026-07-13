"""Unit tests for eval.reporter — no API calls, no pytest markers."""

from eval.mechanical import CheckResult
from eval.reporter import EvalReporter


def _make_result(
    scenario_id="1a-clear-goal",
    prompt_id="1a",
    geval_score=0.8,
    geval_passed=True,
    geval_threshold=0.5,
    geval_reason="Response correctly enforces STOP CONDITION.",
    mechanical_pass=True,
):
    return {
        "scenario_id": scenario_id,
        "prompt_id": prompt_id,
        "input": "Add rate limiting to our Rails API.",
        "output": "STOP CONDITION: I need to search the codebase first.",
        "mechanical": [
            CheckResult(
                field="must_contain: 'STOP CONDITION'",
                passed=mechanical_pass,
                detail=(
                    "'STOP CONDITION' found in output" if mechanical_pass
                    else "'STOP CONDITION' NOT found in output"
                ),
            )
        ],
        "geval_score": geval_score,
        "geval_reason": geval_reason,
        "geval_threshold": geval_threshold,
        "geval_passed": geval_passed,
    }


class TestEvalReporter:

    def test_add_and_count(self):
        reporter = EvalReporter()
        assert len(reporter.results) == 0
        reporter.add(_make_result())
        assert len(reporter.results) == 1

    def test_write_report_creates_file(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result())
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert path.exists()

    def test_report_contains_summary_table(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result())
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "## Summary" in content
        assert "1a-clear-goal" in content

    def test_report_shows_geval_score(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result(geval_score=0.85))
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert "0.85" in path.read_text()

    def test_report_shows_pass_fail_icons(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result(geval_passed=True, mechanical_pass=True))
        reporter.add(_make_result(scenario_id="1a-vague-goal", geval_passed=False, mechanical_pass=False))
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "✅" in content
        assert "❌" in content

    def test_report_contains_judge_reasoning(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result(geval_reason="Response correctly enforces STOP CONDITION."))
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert "Response correctly enforces STOP CONDITION." in path.read_text()

    def test_report_contains_model_output(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result())
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert "STOP CONDITION: I need to search the codebase first." in path.read_text()

    def test_report_contains_mechanical_check_detail(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result(mechanical_pass=False))
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert "NOT found in output" in path.read_text()

    def test_report_contains_phase_names(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result(prompt_id="1a"))
        reporter.add(_make_result(scenario_id="2-first-step", prompt_id="2"))
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "Analysis" in content
        assert "TDD Implementation" in content

    def test_write_report_returns_path(self, tmp_path):
        reporter = EvalReporter()
        reporter.add(_make_result())
        path = tmp_path / "report.md"
        returned = reporter.write_report(path)
        assert returned == path

    def test_empty_reporter_writes_report(self, tmp_path):
        reporter = EvalReporter()
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert path.exists()

    def test_retried_result_shows_retry_info_in_summary(self, tmp_path):
        shot1 = _make_result(geval_passed=False, geval_score=0.20)
        shot2 = _make_result(geval_passed=True, geval_score=0.90)
        shot3 = _make_result(geval_passed=True, geval_score=0.80)
        retried = {
            **shot1,
            "retried": True,
            "shots": [shot1, shot2, shot3],
            "shots_geval_passed": 2,
            "shots_mech_passed": 3,
            "shots_total": 3,
            "geval_passed": True,  # majority verdict
        }
        reporter = EvalReporter()
        reporter.add(retried)
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "2/3" in content

    def test_retried_result_shows_mean_and_stddev_in_summary(self, tmp_path):
        shot1 = _make_result(geval_passed=False, geval_score=0.20)
        shot2 = _make_result(geval_passed=True, geval_score=0.90)
        shot3 = _make_result(geval_passed=True, geval_score=0.80)
        retried = {
            **shot1,
            "retried": True,
            "shots": [shot1, shot2, shot3],
            "shots_geval_passed": 2,
            "shots_mech_passed": 3,
            "shots_total": 3,
            "geval_passed": True,
            "shot_mean": 0.633,
            "shot_stddev": 0.361,
        }
        reporter = EvalReporter()
        reporter.add(retried)
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "0.633 ± 0.361" in content, (
            "Summary table must show 'mean ± stddev' for retried scenarios"
        )

    def test_analyst_notes_section_appears_when_high_variance_scenario_present(self, tmp_path):
        shot1 = _make_result(scenario_id="2-first-step", prompt_id="2",
                             geval_passed=False, geval_score=0.10)
        shot2 = _make_result(scenario_id="2-first-step", prompt_id="2",
                             geval_passed=True, geval_score=0.90)
        shot3 = _make_result(scenario_id="2-first-step", prompt_id="2",
                             geval_passed=True, geval_score=0.80)
        retried = {
            **shot1,
            "retried": True,
            "shots": [shot1, shot2, shot3],
            "shots_geval_passed": 2,
            "shots_mech_passed": 3,
            "shots_total": 3,
            "geval_passed": True,
            "shot_mean": 0.600,
            "shot_stddev": 0.436,  # > 0.2 threshold
        }
        reporter = EvalReporter()
        reporter.add(retried)
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "## Analyst Notes" in content, (
            "Report must include Analyst Notes section when any scenario has stddev > 0.2"
        )
        assert "2-first-step" in content.split("## Analyst Notes")[-1], (
            "Analyst Notes must name the high-variance scenario"
        )

    def test_analyst_notes_absent_when_all_low_variance(self, tmp_path):
        shot1 = _make_result(geval_passed=True, geval_score=0.80)
        shot2 = _make_result(geval_passed=True, geval_score=0.85)
        shot3 = _make_result(geval_passed=True, geval_score=0.90)
        retried = {
            **shot1,
            "retried": True,
            "shots": [shot1, shot2, shot3],
            "shots_geval_passed": 3,
            "shots_mech_passed": 3,
            "shots_total": 3,
            "geval_passed": True,
            "shot_mean": 0.850,
            "shot_stddev": 0.050,  # <= 0.2 threshold
        }
        reporter = EvalReporter()
        reporter.add(retried)
        path = tmp_path / "report.md"
        reporter.write_report(path)
        assert "## Analyst Notes" not in path.read_text(), (
            "Analyst Notes section must not appear when all stddev <= 0.2"
        )

    def test_retried_result_shows_shot_details(self, tmp_path):
        shot1 = _make_result(geval_passed=False, geval_score=0.20)
        shot2 = _make_result(geval_passed=True, geval_score=0.90)
        shot3 = _make_result(geval_passed=True, geval_score=0.80)
        retried = {
            **shot1,
            "retried": True,
            "shots": [shot1, shot2, shot3],
            "shots_geval_passed": 2,
            "shots_mech_passed": 3,
            "shots_total": 3,
            "geval_passed": True,
        }
        reporter = EvalReporter()
        reporter.add(retried)
        path = tmp_path / "report.md"
        reporter.write_report(path)
        content = path.read_text()
        assert "Shot 1" in content
        assert "Shot 2" in content
        assert "Shot 3" in content
