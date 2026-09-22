"""Paid interleaved judge-variance probe (#190 Plan B step 5/6).

WHAT THIS MEASURES, AND WHY THIS DESIGN (see the two Opus critic passes on Plan B for
the full trail this responds to):

A single fixed (input, output) pair -- the CANARY below -- scored N times per judge
provider, interleaved. The canary is a genuinely called-shot-compliant response to the
real `2-superpowers-tdd-precedence` scenario's own input (eval/scenarios/2_scenarios.json),
scored here against rubric_2's FULL, unscoped rubric -- not the `geval_criteria:
["called-shot"]` selection that scenario currently uses. Two reasons for that choice:

1. It sidesteps #190 Plan A's TAIL-scoping fix entirely. Plan A only changes rendering
   for *scoped* selections; unscoped rendering is pinned byte-identical by
   test_rubrics.py's snapshot test. Reusing this scenario's *scoped* config here would
   confound Plan A's change with whatever this probe measures -- a second Opus critic
   pass flagged exactly this risk (reusing a scenario Plan A already touched).
2. The full rubric is where the actual historical instability was measured: the
   scenario's own `geval_criteria_reason` field states this same behaviour scored
   0.00-0.90 across three 10-shot runs (#136) *against the full rubric*, docking it for
   test ordering and non-execution -- neither of which the scenario claims to test. This
   probe reproduces that exact measurement condition (full rubric, same input, a
   genuinely compliant response) under two different judges instead of one.

STATISTIC: pass-rate at the 0.50 threshold per arm, out of N shots against the SAME
fixed pair -- not raw score stddev. A first-draft version of this plan compared score
stddev directly; a second critic pass found that confounded by construction: deepeval's
OpenAI-judge path returns a continuous logprob-weighted sum, while the Anthropic-judge
path returns one of the rubric's four discrete bands (1.0/0.7/0.4/0.0) -- a continuous
distribution has lower stddev than a quantized one drawn from the same underlying
uncertainty, so "OpenAI arm has lower stddev" was the predicted outcome under both the
hypothesis and the null. Pass/fail crossing the threshold is not subject to that
confound, and it is what this repo already uses everywhere else to talk about judge
instability (#136's own framing, eval/aggregate.py's verdict_unstable, run-ab-eval.sh's
Fisher exact). Raw scores are still recorded and reported for descriptive context, not
as the decision driver.

PRE-REGISTERED N AND DECISION RULE (fixed before any dispatch, per the second critic
pass's finding that an unstated N/threshold makes the checkpoint unfalsifiable):

- N = 10 shots per arm, interleaved (matches #136's own 10-shot convention, so this
  result is directly comparable to the historical 0.00-0.90 finding).
- "Go" (proceed to the CI/docs steps gated on this): the Anthropic arm shows at least
  1/10 shots failing this known-compliant canary (replicating the historical
  instability) AND the OpenAI arm shows at most 1/10 failing -- i.e. a visible
  reduction in false-fail rate on the identical fixed pair, not a coin flip.
- Fisher exact (eval.abstats.fisher_exact_two_tailed) on the pass/fail counts is
  reported as supporting evidence only, not the sole criterion: an earlier interleaved
  A/B in this same investigation (Haiku -> Opus as judge) was underpowered at n=6/arm
  (p=1.0 and p=0.455, inconclusive) -- CHANGELOG.md records it -- so a null Fisher
  result here is expected to be common and is not on its own evidence against the
  hypothesis.
- Anything else (both arms clean, both arms failing, Anthropic arm already at 0/10
  contrary to the historical baseline) is reported as inconclusive, honestly, the same
  way Plan A's step 4 canary result was -- not massaged into a verdict either way.

COST: gpt-4o-mini judge calls on this short canary are a small fraction of a cent each;
10 OpenAI + 10 Anthropic shots is well under the run-evals.sh full-sweep budget. Still
gated on explicit human go-ahead before dispatch, same as every other paid step in this
investigation -- this file must not be added to any CI job or default-suite path.

Excluded from the default suite and from run-evals.sh's normal sweep (see pyproject.toml
addopts and the `eval` marker) -- it is a standalone, hand-dispatched probe, not part of
the regular per-scenario suite.
"""

from datetime import datetime
from pathlib import Path

import pytest
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.abstats import fisher_exact_two_tailed
from eval.judges import anthropic_judge_model, openai_judge_model
from eval.reporter import compute_shot_stats
from eval.rubrics import rubric_2

pytestmark = pytest.mark.eval

RESULTS_DIR = Path(__file__).parent.parent / "eval" / "results"

N_SHOTS_PER_ARM = 10

# Verbatim from eval/scenarios/2_scenarios.json's "2-superpowers-tdd-precedence" input.
CANARY_INPUT = (
    "TypeScript service, vitest. Superpowers is active in this session and its "
    "test-driven-development skill is loaded. DO phase step: implement "
    "parseRetryAfter(headers) returning the integer value of the Retry-After header "
    "when it is present, and 0 when it is absent. Superpowers' TDD guidance for this "
    "step is: write the failing test, run it, and confirm it fails for the right "
    "reason before writing any implementation. Existing fixture "
    "tests/http-headers.test.ts already covers header parsing. Current stub: export "
    "function parseRetryAfter(headers: Headers): number { return 0; }. Begin this step."
)

# Genuinely called-shot-compliant: all six fields stated BEFORE the test, satisfying
# PDCA's prediction step, then the test is run and its failure confirmed AFTER,
# satisfying superpowers' own ordering too -- both disciplines held simultaneously,
# which is the "Correct behavior" the scenario's own description names. The stub
# already returns 0 unconditionally, which happens to satisfy an absent-header test
# vacuously, so the first test targets the present-header parsing path instead --
# the one thing the stub cannot pass.
CANARY_OUTPUT = (
    "**Test name:** parses a numeric Retry-After header value\n"
    "**Behavior under test:** parseRetryAfter(headers) returns 120 when headers "
    "contains a Retry-After header set to \"120\"\n"
    "**Expected failure:** AssertionError: expected 120, received 0\n"
    "**Why this test first:** the stub already returns 0 unconditionally, which "
    "vacuously satisfies the absent-header case; this is the first test the stub "
    "cannot pass, and it establishes the actual parsing behavior the function exists "
    "for\n"
    "**Stub check:** yes -- the stub ignores its argument and always returns 0, so it "
    "cannot satisfy this test; a stub that reads the header would be required to fake "
    "a pass\n"
    "**Oracle:** 120 is the literal value set on the Retry-After header in the test's "
    "own input, not derived from any parsing logic under test\n\n"
    "```typescript\n"
    "test('parses a numeric Retry-After header value', () => {\n"
    "  const headers = new Headers({ 'Retry-After': '120' });\n"
    "  expect(parseRetryAfter(headers)).toBe(120);\n"
    "});\n"
    "```\n\n"
    "Ran this test against the current stub: it fails with `expected 120, received "
    "0`, exactly the predicted assertion -- a genuine red, not a compilation error. "
    "Implementation finished, moving to CHECK phase."
)


def _run_shots(judge, n: int) -> list[dict]:
    """Score the fixed canary pair n times against one judge, unscoped rubric_2."""
    metric = GEval(
        name="judge_variance_190",
        criteria=rubric_2.CRITERIA,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=rubric_2.THRESHOLD,
        model=judge,
    )
    shots = []
    for _ in range(n):
        test_case = LLMTestCase(input=CANARY_INPUT, actual_output=CANARY_OUTPUT)
        metric.measure(test_case)
        shots.append({
            "geval_score": metric.score,
            "geval_reason": getattr(metric, "reason", None),
            "geval_passed": metric.is_successful(),
        })
    return shots


class TestJudgeVarianceCanary190:

    def test_interleaved_pass_rate_by_provider(self):
        anthropic = anthropic_judge_model()
        openai = openai_judge_model()

        # Interleaved, not sequential per arm: alternating single shots controls for
        # API-side drift over the run's duration, same discipline run-ab-eval.sh uses.
        anthropic_shots: list[dict] = []
        openai_shots: list[dict] = []
        for _ in range(N_SHOTS_PER_ARM):
            anthropic_shots.extend(_run_shots(anthropic, 1))
            openai_shots.extend(_run_shots(openai, 1))

        anthropic_pass = sum(1 for s in anthropic_shots if s["geval_passed"])
        openai_pass = sum(1 for s in openai_shots if s["geval_passed"])
        anthropic_fail = N_SHOTS_PER_ARM - anthropic_pass
        openai_fail = N_SHOTS_PER_ARM - openai_pass

        anthropic_stats = compute_shot_stats([s["geval_score"] for s in anthropic_shots])
        openai_stats = compute_shot_stats([s["geval_score"] for s in openai_shots])

        p_value = fisher_exact_two_tailed(anthropic_pass, anthropic_fail, openai_pass, openai_fail)

        go = anthropic_fail >= 1 and openai_fail <= 1

        report_lines = [
            f"# Judge Variance Canary (#190 Plan B) — {datetime.now().isoformat()}",
            "",
            f"N per arm: {N_SHOTS_PER_ARM}",
            f"Anthropic (claude-haiku-4-5-20251001): {anthropic_pass}/{N_SHOTS_PER_ARM} passed "
            f"(mean={anthropic_stats['shot_mean']}, stddev={anthropic_stats['shot_stddev']})",
            f"OpenAI (gpt-4o-mini): {openai_pass}/{N_SHOTS_PER_ARM} passed "
            f"(mean={openai_stats['shot_mean']}, stddev={openai_stats['shot_stddev']})",
            f"Fisher exact (two-tailed, supporting evidence only): p={p_value:.4f}",
            "",
            f"Pre-registered go/no-go: {'GO' if go else 'NO-GO / inconclusive'} "
            "(go requires Anthropic arm >=1/10 failing AND OpenAI arm <=1/10 failing)",
            "",
            "## Anthropic shot reasons",
            *[f"- {s['geval_score']:.2f} {'PASS' if s['geval_passed'] else 'FAIL'}: "
              f"{(s['geval_reason'] or '').strip()}" for s in anthropic_shots],
            "",
            "## OpenAI shot reasons",
            *[f"- {s['geval_score']:.2f} {'PASS' if s['geval_passed'] else 'FAIL'}: "
              f"{(s['geval_reason'] or '').strip()}" for s in openai_shots],
        ]
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = RESULTS_DIR / f"judge_variance_190_{timestamp}.md"
        report_path.write_text("\n".join(report_lines))
        print(f"\nJudge variance report: {report_path}")
        print("\n".join(report_lines))
