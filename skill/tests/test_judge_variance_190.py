"""Paid interleaved judge-variance probe (#190 Plan B step 5/6).

WHAT THIS MEASURES, AND WHY THIS DESIGN (see two Opus plan-review passes and four Opus
CHECK-phase passes on Plan B for the full trail this responds to -- earlier versions of
this file were wrong repeatedly, each caught before any dispatch, not after; see
tests/test_judge_variance_logic.py's own docstring for decide_go()'s specific history):

A single fixed (input, output) pair -- the CANARY below -- scored N times per arm,
interleaved across TWO arms:

- "anthropic_prod": Haiku via eval.judges.anthropic_judge_model(), the SAME cached
  builder the real production harness uses -- unset temperature, so Anthropic's own API
  default (1.0) applies, exactly as it does for every real Haiku-judged eval run today.
- "openai": gpt-4o-mini built directly here with temperature=0.0 (already its default).

A third arm ("anthropic_t0": Haiku pinned to temperature=0.0) was considered and
dropped. It would only ever have served as an attribution control -- separating "OpenAI
looks more stable because of the logprob mechanism" from "OpenAI looks more stable
because it happens to run at lower temperature" -- not a standalone fix, and this was a
real correction made mid-investigation: AnthropicModel has no generate_raw_response at
any temperature, so it can never provide deepeval's weighted-averaging mechanism
regardless of how it's configured; a low-variance result on this one canary at T=0
would not have generalized into "pin Haiku's temperature and the problem is solved."
Given that, the narrower attribution value wasn't judged worth the added complexity --
and, as it happened, the arm was also blocked by a real deepeval/anthropic SDK
incompatibility (explicit `temperature` combined with `thinking={'type': 'disabled'}`
raised `TypeError: AsyncMessages.create() got an unexpected keyword argument
'temperature'` against the installed anthropic==1.4.0, confirmed by an actual dispatch
that got one real anthropic_prod shot before hitting this on the first anthropic_t0
shot). Left as a known trail rather than fixed, since the arm no longer earns its cost.

The canary's input is verbatim from the real `2-superpowers-tdd-precedence` scenario
(eval/scenarios/2_scenarios.json), scored against rubric_2's FULL, unscoped rubric --
not the `geval_criteria: ["called-shot"]` selection that scenario currently uses, so
this sidesteps #190 Plan A's TAIL-scoping fix entirely (Plan A only changes rendering
for *scoped* selections; unscoped rendering is pinned byte-identical by
test_rubrics.py's snapshot test). This does NOT reproduce #136's original 0.00-0.90
finding exactly -- those runs generated a fresh executor response each shot, mixing
output variance with judge variance; fixing the output here isolates judge variance
alone, a narrower, cheaper first question.

CANARY OUTPUT: a genuine two-cycle response -- present-header test + GREEN, then
absent-header test + GREEN -- not a single test followed by a completion claim. A
CHECK-phase critic pass found the single-test version was not actually compliant with
the full rubric it's scored against: adding an unconditional implementation without a
second test needing the conditional branch is itself a stub-discipline violation (a
hardcoded `return 120` would have passed the only test that existed); it claimed the
existing fixture already covered behavior the input never says it does; and it violated
the input's own instruction to confirm RED before writing any implementation. The
two-cycle version here matches how this repo's own real scenarios (e.g. 2-first-step)
legitimately earn "Implementation finished, moving to CHECK phase" -- by completing
every test the step specifies in one turn, not by declaring completion after a partial
implementation.

STATISTIC: pass-rate at the 0.50 threshold per arm, out of N shots against the SAME
fixed pair -- not raw score stddev. A second critic pass found stddev confounded by
construction: deepeval's OpenAI-judge path returns a continuous logprob-weighted sum,
while the Anthropic-judge path returns an unweighted integer score /10 -- either way, a
less-constrained distribution reads as lower-variance than a more-constrained one drawn
from identical underlying uncertainty, so "OpenAI arm has lower stddev" was the
predicted outcome under both the hypothesis and the null. Pass/fail crossing the
threshold is not subject to that confound, and it is what this repo already uses
everywhere else to talk about judge instability (#136's own framing,
eval/aggregate.py's verdict_unstable, run-ab-eval.sh's Fisher exact). Raw scores are
still recorded and reported for descriptive context, not as the decision driver.

TEMPERATURE: see the arms described above. A third critic pass found that pinning both
original two arms to temperature=0.0 removed Anthropic's own production variance
entirely (Haiku runs at the API default, 1.0, in every real eval), so the comparison no
longer measured the judge the operator is actually deciding whether to replace. The
anthropic_prod arm fixes this by leaving temperature unset; openai still pins to 0.0,
matching its own real default rather than something imposed for this probe.

PRE-REGISTERED N AND DECISION RULE (fixed before any dispatch -- logic lives in
eval.judge_variance.decide_go, unit-tested in tests/test_judge_variance_logic.py, whose
own docstring records this rule's history: wrong twice, for opposite reasons, before
any real dispatch happened):

- N = 10 shots per arm, interleaved across both arms.
- "Go": decide_go(anthropic_fail, openai_fail). Requires: (1) the Anthropic arm's
  failures are MIXED -- between 2 and 8 of 10, not near either extreme (unanimous or
  near-unanimous failure is uniform disagreement with the judge, not instability -- a
  third critic pass found the floor-only version of this rule returned GO at 10-vs-9,
  which really means the canary is bad); (2) the OpenAI arm fails at most 1 of 10
  times; (3) OpenAI fails strictly fewer times than Anthropic.
- A GO result is DIRECTIONAL, warranting a larger-N confirmation -- not a signal to
  proceed straight to the CI/docs steps it's nominally gated on. It says OpenAI scored
  more consistently than Anthropic on this one input; it does not, on its own, say why
  (the logprob mechanism vs. OpenAI's lower default temperature are both still live
  explanations -- see the dropped anthropic_t0 arm, above).
- READ THE FAILURE REASONS before treating any result as meaningful either way. A
  fourth critic pass, after running this exact canary's TypeScript for real, confirmed
  it still has a genuine, likely-unresolvable tension with the full rubric on THIS
  input: #136's own historical finding was Haiku docking this same input for test
  ordering and non-execution, and the canary's own "Why this test first" field concedes
  the degenerate case can't be tested first without violating stub discipline. If
  Anthropic's failure reasons cite ordering, degenerate-first, or non-execution
  specifically, read the result as "disagreement on an ambiguous criterion for this
  input," not instability -- rewriting the canary a fifth time will not remove this
  tension, since no called-shot response to this exact input can satisfy
  degenerate-first and stub-discipline simultaneously.
- Fisher exact (eval.abstats.fisher_exact_two_tailed) on the anthropic_prod/openai
  pass-fail counts is reported as supporting evidence only, not the sole criterion: an
  earlier interleaved A/B in this same investigation (Haiku -> Opus as judge) was
  underpowered at n=6/arm (p=1.0 and p=0.455, inconclusive) -- CHANGELOG.md records it.
- Anything else is reported as inconclusive, honestly -- not massaged into a verdict.

OBSERVABILITY (S4, added after a third critic pass): each shot is appended to a JSONL
file in eval/results/ as it completes, and the markdown report is written in a
`finally` block from whatever shots exist -- an exception on a late shot must not lose
every earlier shot's data. Score formatting is None-safe, since a judge call can
legitimately return no score. This is what caught the anthropic_t0 SDK failure above
without losing the one real anthropic_prod shot that ran before it.

COST: gpt-4o-mini and Haiku calls on this short canary are a small fraction of a cent
each; 20 shots total is well under the run-evals.sh full-sweep budget. Still gated on
explicit human go-ahead before dispatch, same as every other paid step in this
investigation -- this file must not be added to any CI job or default-suite path.

DISPATCH: run directly, not through run-evals.sh (which would feed this report to
check_eval_ran.py and promote_baseline.py, neither of which understands this probe's
report shape). Needs the `eval` extra, which run-tests.sh's own sync strips:

    cd skill && uv run --extra eval python -m pytest tests/test_judge_variance_190.py -v -s

Excluded from the default suite (see pyproject.toml addopts and the `eval` marker) --
it is a standalone, hand-dispatched probe, not part of the regular per-scenario suite.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from deepeval.metrics import GEval
from deepeval.models import OpenAIModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.abstats import fisher_exact_two_tailed
from eval.judge_variance import decide_go
from eval.judges import OPENAI_JUDGE_MODEL_NAME, anthropic_judge_model
from eval.reporter import compute_shot_stats
from eval.rubrics import rubric_2

pytestmark = pytest.mark.eval

RESULTS_DIR = Path(__file__).parent.parent / "eval" / "results"

N_SHOTS_PER_ARM = 10
PROBE_TEMPERATURE = 0.0

ARM_ANTHROPIC_PROD = "anthropic_prod"
ARM_OPENAI = "openai"

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

# Genuine two-cycle response, compliant against the FULL rubric_2 (see module docstring
# for the violations a single-cycle version had and how this fixes each one).
CANARY_OUTPUT = (
    "**Test name:** parses a numeric Retry-After header value\n"
    "**Behavior under test:** parseRetryAfter(headers) returns 120 when headers "
    "contains a Retry-After header set to \"120\"\n"
    "**Expected failure:** AssertionError: expected +0 to be 120 // Object.is "
    "equality\n"
    "**Why this test first:** the degenerate/zero case (no Retry-After header) already "
    "returns 0 from the current stub, so a test for it would pass vacuously against a "
    "non-implementation and cannot serve as this step's RED; the present-header case is "
    "the first test the stub genuinely cannot satisfy, and it establishes the actual "
    "parsing behavior the function exists for\n"
    "**Stub check:** No -- the stub ignores its argument and always returns 0, so it "
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
    "  return parseInt(headers.get('Retry-After') ?? '', 10);\n"
    "}\n"
    "```\n\n"
    "**Test name:** returns 0 when the Retry-After header is absent\n"
    "**Behavior under test:** parseRetryAfter(headers) returns 0 when headers has no "
    "Retry-After header\n"
    "**Expected failure:** AssertionError: expected NaN to be +0 // Object.is "
    "equality\n"
    "**Why this test first:** deferred against the original stub, since it would have "
    "passed vacuously there; against the implementation just above, it is now a "
    "genuine RED -- parseInt('', 10) returns NaN, not 0\n"
    "**Stub check:** No -- the current implementation returns NaN for an absent "
    "header, not 0, so it cannot satisfy this test\n"
    "**Oracle:** 0 is the literal value the input specifies for an absent header, not "
    "derived from any parsing logic under test\n\n"
    "```typescript\n"
    "test('returns 0 when the Retry-After header is absent', () => {\n"
    "  const headers = new Headers();\n"
    "  expect(parseRetryAfter(headers)).toBe(0);\n"
    "});\n"
    "```\n\n"
    "```typescript\n"
    "export function parseRetryAfter(headers: Headers): number {\n"
    "  const value = headers.get('Retry-After');\n"
    "  return value === null ? 0 : parseInt(value, 10);\n"
    "}\n"
    "```\n\n"
    "Both tests added to the existing fixture tests/http-headers.test.ts.\n\n"
    "Implementation finished, moving to CHECK phase."
)


def _format_score(score: Any) -> str:
    """None-safe score formatting -- a judge call can legitimately return no score."""
    return f"{score:.2f}" if score is not None else "n/a"


def _run_one_shot(judge, arm_name: str, shot_log) -> dict:
    """Score the fixed canary pair once against one judge, unscoped rubric_2.

    `arm_name` is written into the JSONL record itself, not added by the caller after
    the fact -- a fourth CHECK-phase critic pass found an earlier version logged the
    shot before the caller attached which arm it belonged to, so the durability log
    (the whole point of S4's checkpointing) couldn't identify its own rows without
    relying on an undocumented, crash-fragile "position mod 3" convention.
    """
    metric = GEval(
        name="judge_variance_190",
        criteria=rubric_2.CRITERIA,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=rubric_2.THRESHOLD,
        model=judge,
    )
    test_case = LLMTestCase(input=CANARY_INPUT, actual_output=CANARY_OUTPUT)
    metric.measure(test_case)
    shot = {
        "arm": arm_name,
        "geval_score": metric.score,
        "geval_reason": getattr(metric, "reason", None),
        "geval_passed": metric.is_successful(),
    }
    shot_log.write(json.dumps(shot) + "\n")
    shot_log.flush()
    return shot


def _write_report(report_path: Path, shots_by_arm: dict[str, list[dict]], arm_provenance: dict[str, str]) -> None:
    """Best-effort report from whatever shots exist -- called from `finally`, so this
    must not crash on partial or empty data.

    `arm_provenance` carries each arm's actual model name and temperature, read off
    the constructed client -- a fourth CHECK-phase critic pass found the report had
    dropped this after the rewrite that added the third arm, a regression in exactly
    the provenance step 0 of this plan was built to provide.
    """
    lines = [f"# Judge Variance Canary (#190 Plan B) — {datetime.now().isoformat()}", ""]
    lines.append(f"N per arm (target): {N_SHOTS_PER_ARM}")
    for arm, provenance in arm_provenance.items():
        lines.append(f"- {arm}: {provenance}")
    lines.append("")

    stats_by_arm = {}
    for arm, shots in shots_by_arm.items():
        passed = sum(1 for s in shots if s["geval_passed"])
        stats = compute_shot_stats([s["geval_score"] for s in shots if s["geval_score"] is not None])
        stats_by_arm[arm] = {"shots": len(shots), "passed": passed, "fail": len(shots) - passed, **stats}
        lines.append(
            f"{arm}: {passed}/{len(shots)} passed "
            f"(mean={stats['shot_mean']}, stddev={stats['shot_stddev']})"
        )
    lines.append("")

    if ARM_ANTHROPIC_PROD in stats_by_arm and ARM_OPENAI in stats_by_arm:
        a = stats_by_arm[ARM_ANTHROPIC_PROD]
        o = stats_by_arm[ARM_OPENAI]
        if a["shots"] == N_SHOTS_PER_ARM and o["shots"] == N_SHOTS_PER_ARM:
            p_value = fisher_exact_two_tailed(a["passed"], a["fail"], o["passed"], o["fail"])
            go = decide_go(anthropic_fail=a["fail"], openai_fail=o["fail"], n_shots=N_SHOTS_PER_ARM)
            lines.append(f"Fisher exact (anthropic_prod vs openai, supporting evidence only): p={p_value:.4f}")
            go_label = "GO (directional -- see module docstring)" if go else "NO-GO / inconclusive"
            lines.append(f"Pre-registered go/no-go: {go_label}")
        else:
            lines.append(
                f"Incomplete run ({a['shots']}/{N_SHOTS_PER_ARM} anthropic_prod, "
                f"{o['shots']}/{N_SHOTS_PER_ARM} openai shots) -- go/no-go not computed."
            )
    lines.append("")

    for arm, shots in shots_by_arm.items():
        lines.append(f"## {arm} shot reasons")
        for s in shots:
            lines.append(
                f"- {_format_score(s['geval_score'])} {'PASS' if s['geval_passed'] else 'FAIL'}: "
                f"{(s['geval_reason'] or '').strip()}"
            )
        lines.append("")

    report_path.write_text("\n".join(lines))


class TestJudgeVarianceCanary190:

    def test_interleaved_pass_rate_by_provider(self):
        anthropic_prod = anthropic_judge_model()
        openai = OpenAIModel(model=OPENAI_JUDGE_MODEL_NAME, temperature=PROBE_TEMPERATURE)
        arms = {ARM_ANTHROPIC_PROD: anthropic_prod, ARM_OPENAI: openai}

        # Read the actual temperature off each constructed client, not assumed --
        # anthropic_prod's is whatever eval.judges.anthropic_judge_model() leaves it as
        # (production default), which this report must state rather than imply.
        arm_provenance = {
            name: f"{judge.get_model_name()}, temperature={judge.temperature}"
            for name, judge in arms.items()
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shots_path = RESULTS_DIR / f"judge_variance_190_shots_{timestamp}.jsonl"
        report_path = RESULTS_DIR / f"judge_variance_190_{timestamp}.md"

        shots_by_arm: dict[str, list[dict]] = {name: [] for name in arms}
        try:
            with open(shots_path, "a") as shot_log:
                # Interleaved across both arms, not sequential per arm: controls
                # for API-side drift over the run's duration, same discipline
                # run-ab-eval.sh uses.
                for _ in range(N_SHOTS_PER_ARM):
                    for arm_name, judge in arms.items():
                        shot = _run_one_shot(judge, arm_name, shot_log)
                        shots_by_arm[arm_name].append(shot)
        finally:
            _write_report(report_path, shots_by_arm, arm_provenance)
            print(f"\nJudge variance report: {report_path}")
            print(f"Judge variance shot log: {shots_path}")
            print(report_path.read_text())
