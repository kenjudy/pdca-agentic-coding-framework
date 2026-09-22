"""Paid interleaved judge-variance probe (#190 Plan B step 5/6).

WHAT THIS MEASURES, AND WHY THIS DESIGN (see the two Opus plan-review critic passes and
one Opus CHECK-phase critic pass on Plan B for the full trail this responds to):

A single fixed (input, output) pair -- the CANARY below -- scored N times per judge
provider, interleaved. The canary's input is verbatim from the real
`2-superpowers-tdd-precedence` scenario (eval/scenarios/2_scenarios.json), scored here
against rubric_2's FULL, unscoped rubric -- not the `geval_criteria: ["called-shot"]`
selection that scenario currently uses. Two reasons for that choice:

1. It sidesteps #190 Plan A's TAIL-scoping fix entirely. Plan A only changes rendering
   for *scoped* selections; unscoped rendering is pinned byte-identical by
   test_rubrics.py's snapshot test. Reusing this scenario's *scoped* config here would
   confound Plan A's change with whatever this probe measures.
2. The full rubric is closer to where the historical instability was measured: the
   scenario's own `geval_criteria_reason` field states this same *input* scored
   0.00-0.90 across three 10-shot runs (#136) against the full rubric. That said, #136's
   runs generated a FRESH executor response each shot, mixing output variance with judge
   variance; this probe fixes the output and varies only the judge, so it isolates judge
   variance alone -- a narrower, cheaper first question, not a reproduction of #136's
   exact condition. Say so plainly rather than overclaim comparability.

CANARY OUTPUT: the response must be genuinely compliant against every criterion in the
FULL rubric it is scored against here (called shot, degenerate-first, stub discipline,
red-before-green, no-completion-claim, refuse-to-skip -- see rubric_2.CRITERIA_ITEMS),
not just against called-shot the way the real scenario's scoped config requires. A
CHECK-phase critic pass found an earlier version of this canary violated that: it tested
the present-header case without ever justifying skipping the degenerate/zero case in its
own text, falsely claimed to have "ran this test" (impossible in a single-turn harness),
and declared "Implementation finished" while writing no implementation at all -- three
genuine violations that would make Anthropic-arm failures CORRECT verdicts rather than
instability, inverting the whole premise of the go/no-go rule below. The response now:
(a) explicitly argues, in its own "Why this test first" field, why the degenerate/zero
case cannot serve as this step's RED (the stub already returns 0 unconditionally, so a
test for the absent-header case would pass vacuously against a non-implementation,
violating stub discipline rather than satisfying degenerate-first) -- so the judge has
the reasoning within the response itself, not relying on scenario metadata it never
sees; (b) never claims to have executed anything, since a single-turn response cannot;
(c) includes a real implementation that makes the test pass, so "Implementation
finished, moving to CHECK phase" is an earned claim, matching this repo's real scenarios
(e.g. 2-first-step) where a single-turn step legitimately completes with that phrase.

STATISTIC: pass-rate at the 0.50 threshold per arm, out of N shots against the SAME
fixed pair -- not raw score stddev. A first-draft version compared score stddev
directly; a second critic pass found that confounded by construction: deepeval's
OpenAI-judge path returns a continuous logprob-weighted sum, while the Anthropic-judge
path returns an unweighted integer score /10 -- informally anchored to the rubric's
four named bands (1.0/0.7/0.4/0.0) but not hard-quantized to exactly those four values
by the scoring mechanism itself. Either way, a less-constrained distribution reads as
lower-variance than a more-constrained one drawn from identical underlying uncertainty,
so "OpenAI arm has lower stddev" was the predicted outcome under both the hypothesis and
the null. Pass/fail crossing the threshold is not subject to that confound, and it is
what this repo already uses everywhere else to talk about judge instability (#136's own
framing, eval/aggregate.py's verdict_unstable, run-ab-eval.sh's Fisher exact). Raw scores
are still recorded and reported for descriptive context, not as the decision driver.

TEMPERATURE: both judges are constructed here with an explicit, matched temperature
(0.0), NOT via eval.judges' cached anthropic_judge_model()/openai_judge_model()
builders. A CHECK-phase critic pass found deepeval's OpenAIModel defaults to
temperature=0.0 while AnthropicModel leaves temperature unset, so Anthropic's API
default of 1.0 applies -- confounding any pass-rate difference with T=0-vs-T=1, not just
logprob weighting. Building separate, temperature-pinned instances here (rather than
changing eval.judges' shared builders) keeps this probe's fix from perturbing the real
production harness's existing, already-validated Haiku-judged scoring behavior, which
has no reason to change.

PRE-REGISTERED N AND DECISION RULE (fixed before any dispatch; logic lives in
eval.judge_variance.decide_go, unit-tested in tests/test_judge_variance_logic.py so the
rule itself has coverage -- a CHECK-phase critic pass traced the original inline version
of this rule by hand and found it returned GO at 1-vs-1 failures, no reduction at all,
because nothing tested the rule and the bug went unnoticed):

- N = 10 shots per arm, interleaved (matches #136's own 10-shot convention).
- "Go": decide_go(anthropic_fail, openai_fail) -- requires the Anthropic arm to show
  >=2/10 failures (a single failure could be noise; CHANGELOG.md already records an
  underpowered n=6/arm Haiku-vs-Opus A/B, Fisher p=1.0 and p=0.455, from earlier in this
  investigation) AND the OpenAI arm to fail strictly fewer times than Anthropic -- not a
  tie, not a worse result.
- Fisher exact (eval.abstats.fisher_exact_two_tailed) on the pass/fail counts is
  reported as supporting evidence only, not the sole criterion, for the same
  underpowered-n reason above.
- Anything else is reported as inconclusive, honestly, the same way Plan A's step 4
  canary result was -- not massaged into a verdict either way.

COST: gpt-4o-mini judge calls on this short canary are a small fraction of a cent each;
10 OpenAI + 10 Anthropic shots is well under the run-evals.sh full-sweep budget. Still
gated on explicit human go-ahead before dispatch, same as every other paid step in this
investigation -- this file must not be added to any CI job or default-suite path.

DISPATCH: run directly, not through run-evals.sh (which would feed this report to
check_eval_ran.py and promote_baseline.py, neither of which understands this probe's
report shape):

    cd skill && uv run python -m pytest tests/test_judge_variance_190.py -v -s

Excluded from the default suite (see pyproject.toml addopts and the `eval` marker) --
it is a standalone, hand-dispatched probe, not part of the regular per-scenario suite.
"""

from datetime import datetime
from pathlib import Path

import pytest
from deepeval.metrics import GEval
from deepeval.models import AnthropicModel, OpenAIModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.abstats import fisher_exact_two_tailed
from eval.judge_variance import decide_go
from eval.judges import ANTHROPIC_JUDGE_MODEL_NAME, OPENAI_JUDGE_MODEL_NAME
from eval.reporter import compute_shot_stats
from eval.rubrics import rubric_2

pytestmark = pytest.mark.eval

RESULTS_DIR = Path(__file__).parent.parent / "eval" / "results"

N_SHOTS_PER_ARM = 10
PROBE_TEMPERATURE = 0.0

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

# Genuinely compliant against the FULL rubric_2 (see module docstring for the three
# violations a prior version had and how each is fixed here).
CANARY_OUTPUT = (
    "**Test name:** parses a numeric Retry-After header value\n"
    "**Behavior under test:** parseRetryAfter(headers) returns 120 when headers "
    "contains a Retry-After header set to \"120\"\n"
    "**Expected failure:** AssertionError: expected 120, received 0\n"
    "**Why this test first:** the degenerate/zero case (no Retry-After header) already "
    "returns 0 from the current stub, so a test for it would pass vacuously against a "
    "non-implementation and cannot serve as this step's RED; the present-header case is "
    "the first test the stub genuinely cannot satisfy, and it establishes the actual "
    "parsing behavior the function exists for\n"
    "**Stub check:** yes -- the stub ignores its argument and always returns 0, so it "
    "cannot satisfy this test\n"
    "**Oracle:** 120 is the literal value set on the Retry-After header in the test's "
    "own input, not derived from any parsing logic under test\n\n"
    "```typescript\n"
    "test('parses a numeric Retry-After header value', () => {\n"
    "  const headers = new Headers({ 'Retry-After': '120' });\n"
    "  expect(parseRetryAfter(headers)).toBe(120);\n"
    "});\n"
    "```\n\n"
    "```typescript\n"
    "export function parseRetryAfter(headers: Headers): number {\n"
    "  const value = headers.get('Retry-After');\n"
    "  return value === null ? 0 : parseInt(value, 10);\n"
    "}\n"
    "```\n\n"
    "The stub's unconditional `return 0` cannot satisfy the new test, giving the "
    "predicted red; this implementation reads the header and parses it, satisfying the "
    "new test while preserving the absent-header behavior (returns 0) the existing "
    "fixture already covers.\n\n"
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
        # Built directly, temperature-pinned and matched -- not via eval.judges' cached
        # builders, which are shared with the real production harness and must not be
        # perturbed for this one-off comparison. See TEMPERATURE in the module docstring.
        anthropic = AnthropicModel(model=ANTHROPIC_JUDGE_MODEL_NAME, temperature=PROBE_TEMPERATURE)
        openai = OpenAIModel(model=OPENAI_JUDGE_MODEL_NAME, temperature=PROBE_TEMPERATURE)

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

        go = decide_go(anthropic_fail=anthropic_fail, openai_fail=openai_fail)

        report_lines = [
            f"# Judge Variance Canary (#190 Plan B) — {datetime.now().isoformat()}",
            "",
            f"N per arm: {N_SHOTS_PER_ARM}, temperature (both arms): {PROBE_TEMPERATURE}",
            f"Anthropic ({ANTHROPIC_JUDGE_MODEL_NAME}): {anthropic_pass}/{N_SHOTS_PER_ARM} passed "
            f"(mean={anthropic_stats['shot_mean']}, stddev={anthropic_stats['shot_stddev']})",
            f"OpenAI ({OPENAI_JUDGE_MODEL_NAME}): {openai_pass}/{N_SHOTS_PER_ARM} passed "
            f"(mean={openai_stats['shot_mean']}, stddev={openai_stats['shot_stddev']})",
            f"Fisher exact (two-tailed, supporting evidence only): p={p_value:.4f}",
            "",
            f"Pre-registered go/no-go: {'GO' if go else 'NO-GO / inconclusive'} "
            "(go requires Anthropic arm >=2/10 failing AND OpenAI arm failing strictly fewer)",
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
