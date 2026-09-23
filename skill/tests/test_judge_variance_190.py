"""Paid interleaved judge-variance probe (#190 Plan B step 5/6).

WHAT THIS MEASURES, AND WHY THIS DESIGN (see two Opus plan-review passes and four Opus
CHECK-phase passes on Plan B for the full trail this responds to -- earlier versions of
this file were wrong repeatedly, each caught before any dispatch, not after; see
tests/test_judge_variance_logic.py's own docstring for decide_go()'s specific history):

Each test method fixes one (input, output) pair -- CANARY, then CASE2 as a
generalization check (see GENERALIZATION CHECK below) -- and scores it N times per
arm, interleaved across TWO arms:

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

GENERALIZATION CHECK: after the CANARY dispatch returned a directional GO (5/10
anthropic_prod failures vs. 0/10 openai, Fisher p=0.0325 -- see CHANGELOG.md), the
question was whether the pattern holds on a genuinely different, non-hand-crafted
input, or is specific to this one hand-written canary. `test_interleaved_pass_rate_
by_provider_case2_first_step` reuses CASE2_INPUT/CASE2_OUTPUT (see above) -- a real,
previously-scored response to a different real scenario -- rather than writing a
second canary by hand, deliberately avoiding the mistake that took four CHECK-phase
passes to fix for the first one. Same rubric, same statistic, same decide_go rule,
separate report and shot log (suffixed `_case2_`).

NEGATIVE CONTROL (#199, filed after the CASE2 result above): both prior runs only ever
showed either judge a GENUINELY GOOD response or a genuinely flawed-but-plausible one.
OpenAI passed all 20 shots across both. That is exactly what "OpenAI is more reliable"
looks like -- and also exactly what "OpenAI's gpt-4o-mini scoring is lenient regardless
of input" looks like. Nothing so far has shown OpenAI a response any evaluator with the
rubric in hand would call an obvious FAIL. `test_interleaved_pass_rate_by_provider_
negative_control` reuses CANARY_INPUT with a new NEGATIVE_CANARY_OUTPUT: not a minimal
single-field diff from the compliant CANARY_OUTPUT (a near-miss risks being legitimately
borderline, which would make either judge's score uninterpretable for this purpose), but
a response that skips the DO phase's methodology outright -- no called-shot fields, no
test written, no RED phase, an implementation delivered directly, and a false completion
claim. Every criterion in `rubric_2.CRITERIA_ITEMS` is violated at once, by construction,
so confirming it deserves a FAIL is a much lower bar than confirming CANARY_OUTPUT
deserved a PASS was (that took four CHECK-phase passes; this took one read). Pre-
registered interpretation (#199's issue body has the full table): if OpenAI still passes
this at a high rate while Anthropic correctly fails it, that is strong evidence for
leniency over reliability, and this investigation closes without adopting OpenAI
anywhere. `decide_go()` does NOT apply to this test -- it answers "is an improvement
real," not "can this judge fail an obviously bad response at all" -- so this method reads
the raw pass rate and reasoning text directly rather than computing a go/no-go.

COST: gpt-4o-mini and Haiku calls on this short canary are a small fraction of a cent
each; 20 shots per case is well under the run-evals.sh full-sweep budget. Still gated on
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


# A second, real fixed (input, output) pair for a generalization check (#190 Plan B):
# does the anthropic_prod-vs-openai pattern on the hand-written CANARY above hold on a
# genuinely different, non-hand-crafted input too? Reused verbatim from a saved baseline
# report (eval/baselines/report_20260909_174245.md, scenario "2-first-step", unscoped --
# unaffected by Plan A's TAIL-scoping fix, same as CANARY_INPUT/OUTPUT above) rather than
# hand-written, deliberately avoiding the exact mistake that took four CHECK-phase passes
# to fix for the canary above: a hand-crafted "should be compliant" response is easy to
# get subtly wrong. This real response was previously scored 0.70 by Haiku, with the
# judge's own reasoning noting a real, genuine defect (it truncates mid-implementation,
# before Test 4's GREEN phase and before the required handoff phrase) -- used here as-is,
# imperfections included, rather than cleaned up, since the actual question is whether
# both judges score the SAME real (if imperfect) text consistently, not whether this
# specific response is exemplary.
CASE2_INPUT = 'Rails 7 app, PostgreSQL, RSpec + FactoryBot. Adding webhook support. Step 1: Implement WebhookDelivery — accepts event_type (string) and payload (hash), persists to database. File locations confirmed: app/models/webhook_delivery.rb (new), db/migrate/TIMESTAMP_create_webhook_deliveries.rb (new), spec/models/webhook_delivery_spec.rb (new). No existing WebhookDelivery files. ApplicationRecord base class. Start TDD now.'

CASE2_OUTPUT = 'I\'ll check the baseline before writing any code.\n\n```bash\n# Confirm no existing WebhookDelivery files\nfind . -name "*webhook*" -o -name "*Webhook*" 2>/dev/null | grep -v ".git"\n```\n\nAssuming clean baseline (no existing webhook files). Let me begin.\n\n---\n\n## Architectural Safety Check\n\n- **New files:** `app/models/webhook_delivery.rb`, `spec/models/webhook_delivery_spec.rb`, migration — all fit Rails conventions ✅\n- **ApplicationRecord** already exists, we inherit from it ✅\n- **No existing usages** to break ✅\n\nFile locations confirmed:\n- `app/models/webhook_delivery.rb` (new)\n- `db/migrate/TIMESTAMP_create_webhook_deliveries.rb` (new)\n- `spec/models/webhook_delivery_spec.rb` (new)\n\n---\n\n## Full Test List (before writing any code)\n\nWorking out all cases upfront:\n\n1. **Degenerate:** invalid without `event_type` (nil)\n2. **Exception:** invalid without `payload` (nil)\n3. **Exception:** invalid when `event_type` is blank string\n4. **Exception:** `payload` must be a hash (rejects non-hash)\n5. **Happy path:** valid record with `event_type` string + `payload` hash persists\n6. **Happy path:** persisted record round-trips `payload` hash correctly from DB\n\n---\n\n## 🚨 CALLED SHOT — Test 1\n\n- **Test name:** `is invalid without event_type`\n- **Behavior under test:** `WebhookDelivery` with `event_type: nil` fails validation\n- **Expected failure:** `undefined method \'valid?\' for nil` OR more precisely — `NameError: uninitialized constant WebhookDelivery` because the class doesn\'t exist yet\n- **Why this test first:** Degenerate/zero case establishes the API (class exists, has `event_type` attribute, validates presence) before any logic\n- **Stub check:** A no-op stub (`class WebhookDelivery < ApplicationRecord; end`) would *not* satisfy this test — Rails default behavior without `validates :event_type, presence: true` would make the record *valid* with nil (no validation fires), so this test stays genuinely RED until the validation is added. ✅\n\n---\n\n### RED Phase — Test 1\n\n**`spec/models/webhook_delivery_spec.rb`**\n\n```ruby\nrequire \'rails_helper\'\n\nRSpec.describe WebhookDelivery, type: :model do\n  describe \'validations\' do\n    it \'is invalid without event_type\' do\n      delivery = WebhookDelivery.new(payload: { "foo" => "bar" })\n      expect(delivery).not_to be_valid\n      expect(delivery.errors[:event_type]).to include("can\'t be blank")\n    end\n  end\nend\n```\n\nRun it — expected failure:\n\n```\nNameError: uninitialized constant WebhookDelivery\n```\n\n---\n\n### Stub (compile-but-fail stub) — Migration first\n\n**`db/migrate/TIMESTAMP_create_webhook_deliveries.rb`**\n\n```ruby\nclass CreateWebhookDeliveries < ActiveRecord::Migration[7.0]\n  def change\n    create_table :webhook_deliveries do |t|\n      t.string  :event_type, null: false\n      t.jsonb   :payload,    null: false, default: {}\n\n      t.timestamps\n    end\n  end\nend\n```\n\n```bash\nrails db:migrate\nrails db:migrate RAILS_ENV=test\n```\n\n**`app/models/webhook_delivery.rb`** — stub, compiles, no validations yet:\n\n```ruby\nclass WebhookDelivery < ApplicationRecord\nend\n```\n\nRun test now — expected behavioral failure:\n\n```\nexpected #<WebhookDelivery id: nil, event_type: nil, payload: {}> not to be valid\n```\n\nThat\'s our genuine RED (record is valid when it shouldn\'t be). ✅\n\n---\n\n### GREEN Phase — Test 1\n\nAdd the presence validation:\n\n```ruby\nclass WebhookDelivery < ApplicationRecord\n  validates :event_type, presence: true\nend\n```\n\nRun — GREEN ✅\n\n---\n\n## 🚨 CALLED SHOT — Test 2\n\n- **Test name:** `is invalid without payload`\n- **Behavior under test:** `WebhookDelivery` with `payload: nil` fails validation\n- **Expected failure:** `expected #<WebhookDelivery ...> not to be valid` (record is currently valid with nil payload — no validation exists yet)\n- **Why this test first:** Closes the second required field before moving to happy path\n- **Stub check:** Current model has no payload validation, so this will be RED ✅\n\n---\n\n### RED Phase — Test 2\n\nAdd to the `\'validations\'` describe block:\n\n```ruby\nit \'is invalid without payload\' do\n  delivery = WebhookDelivery.new(event_type: \'order.created\', payload: nil)\n  expect(delivery).not_to be_valid\n  expect(delivery.errors[:payload]).to include("can\'t be blank")\nend\n```\n\nRun — RED (nil payload passes with current stub) ✅\n\n---\n\n### GREEN Phase — Test 2\n\n```ruby\nclass WebhookDelivery < ApplicationRecord\n  validates :event_type, presence: true\n  validates :payload,    presence: true\nend\n```\n\nRun both tests — GREEN ✅\n\n---\n\n## 🚨 CALLED SHOT — Test 3\n\n- **Test name:** `is invalid when event_type is blank`\n- **Behavior under test:** Empty string `""` for `event_type` fails validation (presence: true covers this, but we verify explicitly)\n- **Expected failure:** This will actually be **GREEN immediately** — `presence: true` already rejects blank strings\n- **Decision:** Skip — vacuously green against current implementation. Rails `presence: true` handles blank. Move to next non-trivial test.\n\n---\n\n## 🚨 CALLED SHOT — Test 4 (promoted to Test 3)\n\n- **Test name:** `is invalid when payload is not a hash`\n- **Behavior under test:** `payload: "a string"` or `payload: [1,2,3]` fails validation — payload must be a Hash\n- **Expected failure:** `expected #<WebhookDelivery ...> not to be valid` — current model accepts any value for payload as long as it\'s present\n- **Why this test first:** Defines the type contract. A record with `payload: "oops"` currently passes, which is wrong.\n- **Stub check:** Current validation only checks presence, not type — genuinely RED ✅\n\n---\n\n### RED Phase — Test 3 (payload type)\n\n```ruby\nit \'is invalid when payload is not a hash\' do\n  delivery = WebhookDelivery.new(event_type: \'order.created\', payload: "not a hash")\n  expect(delivery).not_to be_valid\n  expect(delivery.errors[:payload]).to include("must be a Hash")\nend\n```\n\nRun — RED (string payload currently passes presence check) ✅\n\n---\n\n### GREEN Phase — Test 3\n\n```ruby\nclass WebhookDelivery < ApplicationRecord\n  validates :event_type, presence: true\n  validates :payload,    presence: true\n  validate  :payload_must_be_hash\n\n  private\n\n  def payload_must_be_hash\n    return if payload.nil? # presence validator handles nil\n    errors.add(:payload, \'must be a Hash\') unless payload.is_a?(Hash)\n  end\nend\n```\n\nRun all three tests — GREEN ✅\n\n---\n\n## 🚨 CALLED SHOT — Test 4 (happy path — persists)\n\n- **Test name:** `is valid with event_type and a payload hash`\n- **Behavior under test:** A record with valid attributes saves to the database\n- **Expected failure:** Should be GREEN immediately — but this is the first test that calls `save` and exercises the actual DB round-trip, making it integration-meaningful\n- **Why this test:** Confirms the migration and model wire up correctly end-to-end. Can\'t be skipped.\n- **Stub check:** All three validations exist — this *should* pass. We run it to confirm the migration worked.\n\n```ruby\nit \'is valid with event_type and a payload hash\' do\n  delivery = WebhookDelivery.new(\n    event_type:'


# Negative control (#199): same scenario/stub as CANARY_INPUT, but the response skips
# the DO phase's methodology outright -- no called-shot fields, no test, no RED phase,
# an implementation delivered directly, and a false completion claim with zero
# verification. Deliberately not a subtle near-miss of CANARY_OUTPUT: see module
# docstring's NEGATIVE CONTROL section for why an unambiguous violation, not a minimal
# diff, is what this spike actually needs.
NEGATIVE_CANARY_OUTPUT = (
    "Here's the implementation:\n\n"
    "```typescript\n"
    "export function parseRetryAfter(headers: Headers): number {\n"
    "  const value = headers.get('Retry-After');\n"
    "  return value === null ? 0 : parseInt(value, 10);\n"
    "}\n"
    "```\n\n"
    "This correctly returns 0 when the header is absent and parses the numeric value "
    "when present.\n\n"
    "Implementation finished, moving to CHECK phase."
)


def _format_score(score: Any) -> str:
    """None-safe score formatting -- a judge call can legitimately return no score."""
    return f"{score:.2f}" if score is not None else "n/a"


def _run_one_shot(judge, arm_name: str, shot_log, input_text: str, output_text: str) -> dict:
    """Score one fixed (input, output) pair once against one judge, unscoped rubric_2.

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
    test_case = LLMTestCase(input=input_text, actual_output=output_text)
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


def _write_report(
    report_path: Path,
    shots_by_arm: dict[str, list[dict]],
    arm_provenance: dict[str, str],
    case_name: str = "Canary",
    apply_decision_rule: bool = True,
) -> None:
    """Best-effort report from whatever shots exist -- called from `finally`, so this
    must not crash on partial or empty data.

    `arm_provenance` carries each arm's actual model name and temperature, read off
    the constructed client -- a fourth CHECK-phase critic pass found the report had
    dropped this after the rewrite that added the third arm, a regression in exactly
    the provenance step 0 of this plan was built to provide.

    `apply_decision_rule=False` (used by the #199 negative-control test) still reports
    Fisher's p-value as supporting evidence but omits `decide_go()` -- that rule answers
    "is an improvement real," not "can this judge fail an obviously bad response at all,"
    and applying it to a run with a different question would print a GO/NO-GO label that
    doesn't mean what it means everywhere else in this file's reports.
    """
    lines = [f"# Judge Variance {case_name} (#190 Plan B) — {datetime.now().isoformat()}", ""]
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
            lines.append(f"Fisher exact (anthropic_prod vs openai, supporting evidence only): p={p_value:.4f}")
            if apply_decision_rule:
                go = decide_go(anthropic_fail=a["fail"], openai_fail=o["fail"], n_shots=N_SHOTS_PER_ARM)
                go_label = "GO (directional -- see module docstring)" if go else "NO-GO / inconclusive"
                lines.append(f"Pre-registered go/no-go: {go_label}")
            else:
                lines.append(
                    "decide_go() not applicable -- diagnostic run, see #199: read pass "
                    "rate and reasoning text directly."
                )
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
                        shot = _run_one_shot(judge, arm_name, shot_log, CANARY_INPUT, CANARY_OUTPUT)
                        shots_by_arm[arm_name].append(shot)
        finally:
            _write_report(report_path, shots_by_arm, arm_provenance, case_name="Canary")
            print(f"\nJudge variance report: {report_path}")
            print(f"Judge variance shot log: {shots_path}")
            print(report_path.read_text())

    def test_interleaved_pass_rate_by_provider_case2_first_step(self):
        """Generalization check: does the pattern on the hand-written CANARY hold on a
        real, non-hand-crafted response too? See CASE2_INPUT/CASE2_OUTPUT above."""
        anthropic_prod = anthropic_judge_model()
        openai = OpenAIModel(model=OPENAI_JUDGE_MODEL_NAME, temperature=PROBE_TEMPERATURE)
        arms = {ARM_ANTHROPIC_PROD: anthropic_prod, ARM_OPENAI: openai}

        arm_provenance = {
            name: f"{judge.get_model_name()}, temperature={judge.temperature}"
            for name, judge in arms.items()
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shots_path = RESULTS_DIR / f"judge_variance_190_case2_shots_{timestamp}.jsonl"
        report_path = RESULTS_DIR / f"judge_variance_190_case2_{timestamp}.md"

        shots_by_arm: dict[str, list[dict]] = {name: [] for name in arms}
        try:
            with open(shots_path, "a") as shot_log:
                for _ in range(N_SHOTS_PER_ARM):
                    for arm_name, judge in arms.items():
                        shot = _run_one_shot(judge, arm_name, shot_log, CASE2_INPUT, CASE2_OUTPUT)
                        shots_by_arm[arm_name].append(shot)
        finally:
            _write_report(report_path, shots_by_arm, arm_provenance, case_name="Case2 (2-first-step)")
            print(f"\nJudge variance report: {report_path}")
            print(f"Judge variance shot log: {shots_path}")
            print(report_path.read_text())

    def test_interleaved_pass_rate_by_provider_negative_control(self):
        """#199: does either judge ever fail an obviously bad response, or has every
        prior run just never shown OpenAI one? See NEGATIVE_CANARY_OUTPUT and the module
        docstring's NEGATIVE CONTROL section."""
        anthropic_prod = anthropic_judge_model()
        openai = OpenAIModel(model=OPENAI_JUDGE_MODEL_NAME, temperature=PROBE_TEMPERATURE)
        arms = {ARM_ANTHROPIC_PROD: anthropic_prod, ARM_OPENAI: openai}

        arm_provenance = {
            name: f"{judge.get_model_name()}, temperature={judge.temperature}"
            for name, judge in arms.items()
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shots_path = RESULTS_DIR / f"judge_variance_190_negctrl_shots_{timestamp}.jsonl"
        report_path = RESULTS_DIR / f"judge_variance_190_negctrl_{timestamp}.md"

        shots_by_arm: dict[str, list[dict]] = {name: [] for name in arms}
        try:
            with open(shots_path, "a") as shot_log:
                for _ in range(N_SHOTS_PER_ARM):
                    for arm_name, judge in arms.items():
                        shot = _run_one_shot(judge, arm_name, shot_log, CANARY_INPUT, NEGATIVE_CANARY_OUTPUT)
                        shots_by_arm[arm_name].append(shot)
        finally:
            _write_report(
                report_path,
                shots_by_arm,
                arm_provenance,
                case_name="Negative Control",
                apply_decision_rule=False,
            )
            print(f"\nJudge variance report: {report_path}")
            print(f"Judge variance shot log: {shots_path}")
            print(report_path.read_text())
