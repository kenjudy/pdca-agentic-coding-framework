"""LLM-as-judge evaluation tests for PDCA phase prompts.

These tests invoke the real Anthropic API and use DeepEval GEval for
rubric-based scoring. They are expensive (~$2-5 per full run) and slow.

Run with:
    uv run ./run-evals.sh

Do NOT run in CI — they are excluded from the default test suite via the
`eval` pytest marker.

Results are written to eval/results/report_<timestamp>.md after each run.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from deepeval.metrics import GEval
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.executor import run_phase
from eval.mechanical import check_mechanical
from eval.reporter import EvalReporter, compute_shot_stats
from eval.rubrics.rubric_1a import CRITERIA as CRITERIA_1A
from eval.rubrics.rubric_1a import THRESHOLD as THRESHOLD_1A
from eval.rubrics.rubric_1b import CRITERIA as CRITERIA_1B
from eval.rubrics.rubric_1b import THRESHOLD as THRESHOLD_1B
from eval.rubrics.rubric_2 import CRITERIA as CRITERIA_2
from eval.rubrics.rubric_2 import THRESHOLD as THRESHOLD_2
from eval.rubrics.rubric_3 import CRITERIA as CRITERIA_3
from eval.rubrics.rubric_3 import THRESHOLD as THRESHOLD_3
from eval.rubrics.rubric_4 import CRITERIA as CRITERIA_4
from eval.rubrics.rubric_4 import THRESHOLD as THRESHOLD_4

JUDGE_MODEL = AnthropicModel(model="claude-haiku-4-5-20251001")

pytestmark = pytest.mark.eval

CLAUDE_SKILL_DIR = Path(__file__).parent.parent
SCENARIOS_DIR = CLAUDE_SKILL_DIR / "eval" / "scenarios"
PHASE_PROMPTS_DIR = CLAUDE_SKILL_DIR / "pdca-framework" / "references"
RESULTS_DIR = CLAUDE_SKILL_DIR / "eval" / "results"

PROMPT_FILE = {
    "1a": "plan-prompts.md",
    "1b": "plan-prompts.md",
    "2": "do-prompts.md",
    "3": "check-prompts.md",
    "4": "act-prompts.md",
}


def load_scenarios(prompt_id: str) -> list[dict]:
    scenario_file = SCENARIOS_DIR / f"{prompt_id}_scenarios.json"
    with open(scenario_file) as f:
        return json.load(f)


def _rubric_for_prompt(prompt_id: str) -> tuple[str, float]:
    rubrics = {
        "1a": (CRITERIA_1A, THRESHOLD_1A),
        "1b": (CRITERIA_1B, THRESHOLD_1B),
        "2":  (CRITERIA_2,  THRESHOLD_2),
        "3":  (CRITERIA_3,  THRESHOLD_3),
        "4":  (CRITERIA_4,  THRESHOLD_4),
    }
    if prompt_id not in rubrics:
        raise ValueError(f"No rubric registered for prompt_id: {prompt_id!r}")
    return rubrics[prompt_id]


def _run_scenario(scenario: dict, include_skill_prompt: bool = True) -> dict:
    prompt_id = scenario["prompt_id"]
    phase_prompt_path = PHASE_PROMPTS_DIR / PROMPT_FILE[prompt_id]

    output = run_phase(phase_prompt_path, scenario["input"], include_skill_prompt=include_skill_prompt)
    mechanical_results = check_mechanical(output, scenario["expected_signals"])

    if scenario["expected_signals"].get("skip_geval"):
        return {
            "scenario_id": scenario["scenario_id"],
            "prompt_id": prompt_id,
            "input": scenario["input"],
            "output": output,
            "mechanical": mechanical_results,
            "geval_score": None,
            "geval_reason": "GEval skipped for this scenario type",
            "geval_threshold": 0.0,
            "geval_passed": True,
        }

    criteria, threshold = _rubric_for_prompt(prompt_id)
    metric = GEval(
        name=f"pdca_{prompt_id}_compliance",
        criteria=criteria,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=threshold,
        model=JUDGE_MODEL,
    )
    test_case = LLMTestCase(input=scenario["input"], actual_output=output)
    metric.measure(test_case)

    return {
        "scenario_id": scenario["scenario_id"],
        "prompt_id": prompt_id,
        "input": scenario["input"],
        "output": output,
        "mechanical": mechanical_results,
        "geval_score": metric.score,
        "geval_reason": getattr(metric, "reason", None),
        "geval_threshold": threshold,
        "geval_passed": metric.is_successful(),
    }


# ---------------------------------------------------------------------------
# Session fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def reporter():
    return EvalReporter()


@pytest.fixture(autouse=True, scope="session")
def write_report(reporter):
    yield
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reporter.write_report(RESULTS_DIR / f"report_{timestamp}.md")
    print(f"\nEval report: {report_path}")


# ---------------------------------------------------------------------------
# Shared assertion helper
# ---------------------------------------------------------------------------

def _result_passed(result: dict) -> tuple[bool, bool]:
    """Return (mech_passed, geval_passed) for a single result."""
    mech_passed = not any(not c.passed for c in result["mechanical"])
    geval_passed = result["geval_passed"]
    return mech_passed, geval_passed


def _assert_and_store(scenario: dict, reporter: EvalReporter) -> None:
    result = _run_scenario(scenario)
    reporter.add(result)

    mech_ok, geval_ok = _result_passed(result)

    if mech_ok and geval_ok:
        return

    # First shot failed — run 2 more shots and use majority voting (≥2/3).
    all_results = [result]
    for _ in range(2):
        r = _run_scenario(scenario)
        all_results.append(r)

    mech_pass_count = sum(1 for r in all_results if _result_passed(r)[0])
    geval_pass_count = sum(1 for r in all_results if _result_passed(r)[1])

    shot_scores = [r["geval_score"] for r in all_results if r["geval_score"] is not None]
    stats = compute_shot_stats(shot_scores) if shot_scores else {"shot_mean": None, "shot_stddev": None}

    # Replace reporter entry with retry-aware summary so report reflects true verdict.
    reporter.results.pop()
    reporter.add({
        **result,
        "retried": True,
        "shots": all_results,
        "shots_geval_passed": geval_pass_count,
        "shots_mech_passed": mech_pass_count,
        "shots_total": 3,
        "geval_passed": geval_pass_count >= 2,
        **stats,
    })

    sid = result["scenario_id"]
    assert mech_pass_count >= 2, (
        f"[{sid}] Mechanical checks failed in majority of shots ({mech_pass_count}/3):\n"
        + "\n".join(
            f"  shot {i+1}: {c.detail}"
            for i, r in enumerate(all_results)
            for c in r["mechanical"] if not c.passed
        )
    )
    assert geval_pass_count >= 2, (
        f"[{sid}] GEval failed in majority of shots ({geval_pass_count}/3).\n"
        + "\n".join(
            f"  shot {i+1}: score={r['geval_score']:.2f}  {r.get('geval_reason', '')}"
            for i, r in enumerate(all_results)
            if not _result_passed(r)[1] and r["geval_score"] is not None
        )
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------

class TestPrompt1aEvals:
    """End-to-end LLM eval for PDCA prompt 1a (Analysis Phase)."""

    @pytest.mark.parametrize("scenario", load_scenarios("1a"), ids=lambda s: s["scenario_id"])
    def test_1a_scenario(self, scenario, reporter):
        _assert_and_store(scenario, reporter)


class TestPrompt1bEvals:
    """End-to-end LLM eval for PDCA prompt 1b (Planning Phase)."""

    @pytest.mark.parametrize("scenario", load_scenarios("1b"), ids=lambda s: s["scenario_id"])
    def test_1b_scenario(self, scenario, reporter):
        _assert_and_store(scenario, reporter)


class TestPrompt2Evals:
    """End-to-end LLM eval for PDCA prompt 2 (DO / TDD Implementation)."""

    @pytest.mark.parametrize("scenario", load_scenarios("2"), ids=lambda s: s["scenario_id"])
    def test_2_scenario(self, scenario, reporter):
        _assert_and_store(scenario, reporter)


class TestPrompt3Evals:
    """End-to-end LLM eval for PDCA prompt 3 (Check Phase)."""

    @pytest.mark.parametrize("scenario", load_scenarios("3"), ids=lambda s: s["scenario_id"])
    def test_3_scenario(self, scenario, reporter):
        _assert_and_store(scenario, reporter)


class TestBaselineComparison:
    """Validate that the skill prompt causes measurable improvement over no prompt.

    Runs all 15 scenarios twice: once with the skill prompt (standard) and once
    without (include_skill_prompt=False). Asserts that the prompt produces a
    higher or equal GEval score for at least 10 of the 15 scenarios.

    A failure here means the prompt is not causing the behaviors the rubrics
    measure -- investigate before concluding the prompts need revision, as
    LLM-judge variance can affect individual scores. Re-run 2-3 times if the
    count is close to the threshold.

    Requires ANTHROPIC_API_KEY. Run with: bash run-evals.sh -k TestBaselineComparison
    Cost: approximately doubles the standard eval run cost.
    """

    def test_baseline_comparison_shows_positive_delta_for_majority_of_scenarios(self, reporter):
        positive_delta_count = 0
        skipped_count = 0
        results = []

        for prompt_id in ["1a", "1b", "2", "3", "4"]:
            for scenario in load_scenarios(prompt_id):
                if scenario["expected_signals"].get("skip_geval"):
                    continue

                with_result = _run_scenario(scenario, include_skill_prompt=True)
                without_result = _run_scenario(scenario, include_skill_prompt=False)

                with_score = with_result["geval_score"]
                without_score = without_result["geval_score"]

                # Skip pair if either score is None (DeepEval parse error)
                if with_score is None or without_score is None:
                    skipped_count += 1
                    continue

                delta = with_score - without_score
                if delta >= 0:
                    positive_delta_count += 1
                results.append({
                    "scenario_id": scenario["scenario_id"],
                    "with_score": round(with_score, 3),
                    "without_score": round(without_score, 3),
                    "delta": round(delta, 3),
                })

        total = len(results)
        detail = "\n".join(
            f"  {r['scenario_id']}: with={r['with_score']} without={r['without_score']} delta={r['delta']:+.3f}"
            for r in sorted(results, key=lambda r: r["delta"])
        )
        skip_note = f" ({skipped_count} skipped due to judge errors)" if skipped_count else ""
        assert positive_delta_count >= 10, (
            f"Only {positive_delta_count}/{total} scenarios showed non-negative delta{skip_note}.\n"
            f"Per-scenario scores (sorted by delta):\n{detail}"
        )


class TestPrompt4Evals:
    """End-to-end LLM eval for PDCA prompt 4 (Act / Retrospection)."""

    @pytest.mark.parametrize("scenario", load_scenarios("4"), ids=lambda s: s["scenario_id"])
    def test_4_scenario(self, scenario, reporter):
        _assert_and_store(scenario, reporter)
