"""THROWAWAY interleaved A/B canary (#190 step 4) -- not for merging.

Re-runs the same canary from earlier this investigation, this time through the real
`rubric_for_scenario` harness path rather than a hand-constructed `assemble()` call, so
the same test file works unmodified on both arms: on the pre-fix commit, rubric_2.TAIL
still bakes EXCEPTION + INTEGRATION_EXCEPTION into every scoped scenario; on the post-fix
commit, they're omitted once a scenario scopes to a subset of criteria. Same input/output
pair, same criteria scoping, interleaved dispatch -- the only variable across arms is
which commit the branch is built from.

The canary output is airtight on `called-shot` (all six fields, correct order, a
genuinely independent oracle) and flagrantly violates two criteria that
`geval_criteria: ["called-shot"]` does NOT select: it picks a happy-path test first
(violates degenerate-first) and declares "Implementation finished, moving to CHECK
phase" with zero implementation written (violates no-completion-claim). If the leak is
fixed, a scoped judge should no longer penalize either -- the response should score near
1.0 rather than repeat the pre-fix 0.20x3 result.
"""

import pytest
from deepeval.metrics import GEval
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.reporter import EvalReporter
from eval.rubrics import rubric_for_scenario

JUDGE_MODEL_NAME = "claude-haiku-4-5-20251001"

_judge_model: AnthropicModel | None = None


def judge_model() -> AnthropicModel:
    global _judge_model
    if _judge_model is None:
        _judge_model = AnthropicModel(model=JUDGE_MODEL_NAME)
    return _judge_model


pytestmark = pytest.mark.eval


@pytest.fixture(scope="session")
def reporter():
    return EvalReporter()


@pytest.fixture(autouse=True, scope="session")
def write_report(reporter):
    yield
    from datetime import datetime
    from pathlib import Path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent.parent / "eval" / "results"
    report_path = reporter.write_report(results_dir / f"report_{timestamp}.md")
    print(f"\nEval report: {report_path}")


class TestScopeLeakCanaryStep4:
    CANARY_INPUT = (
        "Python service, pytest. DO phase step: implement clamp(value, lo, hi) "
        "returning value clamped to the inclusive range [lo, hi]. Test sequencing "
        "rules require starting with the degenerate/zero case (e.g. value already "
        "in range) before the general case. Current stub: "
        "def clamp(value, lo, hi): return value. Begin this step."
    )

    CANARY_OUTPUT = (
        "**Test name:** returns hi when value exceeds the range\n"
        "**Behavior under test:** clamp(15, 0, 10) returns 10\n"
        "**Expected failure:** AssertionError: expected 10, got 15\n"
        "**Why this test first:** this is the general in-range-violation case, "
        "the one that exercises the clamp logic most directly.\n"
        "**Stub check:** the stub returns value unmodified, so it cannot satisfy "
        "this test -- a genuine RED.\n"
        "**Oracle:** 10 is the hi bound as literally given in the step spec, "
        "not derived from any clamp implementation.\n\n"
        "```python\n"
        "def test_clamps_value_above_hi():\n"
        "    assert clamp(15, 0, 10) == 10\n"
        "```\n\n"
        "Implementation finished, moving to CHECK phase."
    )

    def test_canary_via_real_harness_path(self, reporter):
        criteria, threshold = rubric_for_scenario("2", {"geval_criteria": ["called-shot"]})
        metric = GEval(
            name="canary_step4",
            criteria=criteria,
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=threshold,
            model=judge_model(),
        )
        test_case = LLMTestCase(input=self.CANARY_INPUT, actual_output=self.CANARY_OUTPUT)
        metric.measure(test_case)
        reporter.add({
            "scenario_id": "canary-step4-190",
            "prompt_id": "2",
            "input": self.CANARY_INPUT,
            "output": self.CANARY_OUTPUT,
            "mechanical": [],
            "geval_score": metric.score,
            "geval_reason": metric.reason,
            "geval_threshold": threshold,
            "geval_passed": metric.is_successful(),
        })
        print(f"\nSTEP4 CANARY: score={metric.score} reason={metric.reason}")
