# PDCA Skill Eval Harness

LLM-as-judge evaluation suite for the five PDCA phase prompts. Verifies that the
skill's prompts produce compliant, behaviorally-correct responses across a range
of realistic scenarios.

---

## Design

The harness uses a two-tier check strategy:

| Tier | What it checks | Cost |
|------|---------------|------|
| **Mechanical** (`check_mechanical`) | String-level signals: required phrases present, forbidden phrases absent, called-shot fields all present | Zero — no API calls |
| **GEval** (DeepEval + Claude Haiku) | Rubric-based compliance: sequence, structure, refusal to skip steps, specificity | ~$0.15–0.40 per scenario |

Mechanical checks run first and are cheap. GEval catches behavioral compliance that
string matching cannot — e.g., whether critical moments are session-specific vs. generic,
or whether a plan is truly atomic vs. just numbered.

**Judge model:** `claude-haiku-4-5-20251001`
**Estimated full-run cost:** ~$2–5 (15 scenarios × two API calls each: one for the evaluated
model response, one for the GEval judge)

**Fidelity note:** The executor sends the full phase prompt file as system context
(e.g., `plan-prompts.md` contains both 1a and 1b). The model sees both phases and must
apply the correct one based on the scenario input. This mirrors real skill usage.

---

## Running Evals

**Prerequisites:** Python 3.11+, uv, ANTHROPIC_API_KEY in `.env`

```bash
cd skill
uv sync --extra eval
cp .env.example .env        # fill in ANTHROPIC_API_KEY
bash run-evals.sh           # all 15 scenarios
```

Run a single prompt's tests:

```bash
bash run-evals.sh tests/test_evals.py::TestPrompt2Evals
```

Run a single scenario by ID:

```bash
cd skill && uv run python -m pytest tests/test_evals.py -m eval -k "2-skip-tests-request" -v
```

Unit tests (no API calls, always run in CI):

```bash
bash run-tests.sh
```

---

## Prompt Coverage

| Prompt | File | Scenarios | Key behaviors tested |
|--------|------|-----------|----------------------|
| 1a — Analysis | `plan-prompts.md` | `1a_scenarios.json` | STOP CONDITION enforced, no premature solutions, external validation flagged |
| 1b — Planning | `plan-prompts.md` | `1b_scenarios.json` | Atomic steps, test list produced, refactor:/feat: separation |
| 2 — DO (TDD) | `do-prompts.md` | `2_scenarios.json` | Called shot (all 3 fields), degenerate case first, refuses to skip tests |
| 3 — Check | `check-prompts.md` | `3_scenarios.json` | All checklist sections, explicit Status: verdict, Ready to close: with reasoning |
| 4 — Act (Retro) | `act-prompts.md` | `4_scenarios.json` | Session-specific critical moments, Start/Stop/Keep, ONE thing answered |

---

## Signal Selection Guide

Use this to decide how to capture a behavioral expectation:

**Use `must_contain`** when the prompt template uses a literal label the model must echo
back (e.g., `"Status:"`, `"Ready to close:"`, `"Start doing:"`). These are cheap and
reliable.

**Use `must_not_contain`** when a forbidden phrase is a hard STOP rule in the prompt
(e.g., `"complete"` / `"done"` for the DO phase, premature code in the analysis phase).
Keep phrases specific enough to avoid false positives.

**Use `called_shot_required: true`** when all three called-shot fields (`"Test name:"`,
`"Behavior under test:"`, `"Expected failure:"`) must appear together. This is the
mechanical check for DO phase scenarios.

**Use GEval (rubric only)** when compliance requires evaluating sequence, specificity,
or structure that can't be captured by string matching alone — e.g., whether critical
moments reference the actual session, whether steps are truly atomic, or whether
analysis correctly defers a solution.

---

## Adding a New Prompt's Evals

1. **Scenario file** — create `eval/scenarios/<prompt_id>_scenarios.json` with at least
   3 scenarios. Each scenario needs: `prompt_id`, `scenario_id`, `description`, `input`,
   `expected_signals` (`must_contain`, `must_not_contain`, `called_shot_required`).
   Write `description` to explain the edge case and what a compliant response should do
   differently from a non-compliant one.

2. **Rubric file** — create `eval/rubrics/rubric_<prompt_id>.py` with `CRITERIA` (string)
   and `THRESHOLD` (float, typically 0.5). The criteria must ask the judge for Strengths,
   Weaknesses, and Reasoning before the score. See any existing rubric for the pattern.

3. **Route the prompt file** — add `"<prompt_id>": "<filename>.md"` to the `PROMPT_FILE`
   dict in `tests/test_evals.py`.

4. **Register the rubric** — add the import and entry to `_rubric_for_prompt` in
   `tests/test_evals.py`.

5. **Add a test class** — add `TestPrompt<N>Evals` with a parametrized test method
   following the existing pattern.

6. **Run the new scenarios** and verify the harness executes without errors:
   ```bash
   bash run-evals.sh tests/test_evals.py::TestPrompt<N>Evals
   ```
