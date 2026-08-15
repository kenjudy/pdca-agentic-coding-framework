# Implementation Plan: Repair Mechanical Signal Matching in the Eval Harness

> **Working artifact.** This file exists so the plan survives across sessions and threads.
> Delete it before merging to `main`.
>
> **Produced by:** PDCA PLAN phase (1a analysis + 1b plan), Opus 5, 2026-08-15
> **Origin:** ACT retrospective of the ponytail interop cycle. Filed as
> [#111](https://github.com/kenjudy/pdca-agentic-coding-framework/issues/111).
>
> **Progress:** Step 0 complete — baseline below. Next: Step 1.

---

## Goal

After this cycle, `check_mechanical` matches signal phrases against the *content* of a model
response rather than its markdown formatting — so the anti-rubber-stamp guard actually fires, and
cosmetic emphasis differences stop being scored as non-compliance.

---

## Background for a fresh session

### The defect, in one line

`check_mechanical` (`skill/eval/mechanical.py:30-44`) does raw Python `in` substring matching
against markdown-formatted model output. The CHECK template teaches the model to write
`**Status:** Complete`. Literal matching against that string produces two failures in opposite
directions.

### Defect 1 — the anti-rubber-stamp guard cannot fire (false negative on violations)

```python
>>> "Status: Complete" in "**Status:** Complete"
False
```

`must_not_contain: ["Status: Complete"]` appears in **two** scenarios — `3-todos-remaining` and
`3-missing-documentation`. Both exist to catch a model certifying unfinished work. Neither can,
because the `**` sits between `Status:` and `Complete`. A model that declares completion over
three unresolved TODOs passes both scenarios, provided it uses the bold formatting the template
itself taught it.

This is the framework's central failure mode, and its gate has never been able to detect it.

### Defect 2 — cosmetic emphasis scored as non-compliance (false positive on compliance)

```python
>>> "Status:" in "**Status**: Complete"     # colon outside the bold
False
```

Affects every phrase whose signal ends in a colon — roughly 20 of the 51 signal phrases in the
suite, plus the four internal fields of `called_shot_required`. Observed live: during the ponytail
cycle, `2-after-passing-test` shot 3 failed on `'Why this test first:' NOT found` while the GEval
judge scored that same response **0.90** and praised its called-shot discipline.

**A meaningful share of what this repo has been calling eval flakiness is probably this defect.**
The judge layer largely agrees with itself across runs; the cheap deterministic layer underneath
does not.

### Evidence base

Gathered during the ponytail cycle, 2026-08-15:

- 36 runs of `3-all-complete`: unmodified control 15/18 (83%), i.e. it fails on prompt text nobody
  changed. Two interleaved A/B pairs failed on *both* arms simultaneously. Control vs. the Step 8
  build, Fisher exact: **p = 0.2098** — not attributable. (Originally reported as "p ≈ 0.11" by
  estimation; that number was wrong, which is why `eval/abstats.py` now exists.)
- `TestPrompt2Evals` `2-after-passing-test`: GEval passed 3/3 while mechanical passed 1/3.
- Full signal inventory: 51 phrases across the 5 scenario files (see Step 0).

---

## Step 0 baseline (recorded 2026-08-15, before any matcher edit)

**Unit gates:** 140 passed, 153 subtests passed, ruff clean, mypy clean across 19 source files.

**Signal inventory:** 51 phrases across the 5 scenario files.

| Category | Count | Exposure |
|---|---|---|
| Phrases ending in `:` | 19 | False negative — `**X**:` styling defeats the match |
| Phrases containing `": "` | 2 | **False positive — the vacuous guard.** Both are `must_not_contain: "Status: Complete"`, in `3-todos-remaining` and `3-missing-documentation` |
| Scenarios using `called_shot_required` | 2 | 4 colon-terminated fields each — `2-after-passing-test`, `2-ponytail-precedence` |

**Test-list predictions verified against the live checker** (all five as the plan states):

| Test | Pre-change | Plan says |
|---|---|---|
| #1 `must_not_contain` vs `**Status:** Complete` | `passed=True` | passes — the bug ✓ |
| #2 `must_contain "Status:"` vs `**Status**: Complete` | `passed=False` | fails — the bug ✓ |
| #3 `called_shot_required` vs `**Test name**:` | `passed=False` | fails — the bug ✓ |
| #4 `def deliver_webhook` | `passed=True` | guard ✓ |
| #5 inline-code `` `bd update` `` | `passed=True` | guard ✓ |

**Plan defect found and corrected at Step 0.** Step 0 as written asked to record "which scenarios
currently pass," which requires an API key — contradicting the plan's own claim that Steps 0–7 need
none. The eval baseline is **deferred to Step 8**, where the key is required regardless. The
deterministic baseline above is what Steps 1–7 actually need.

---

## Decisions already made (do not relitigate)

1. **Strip `*` only — not `_`, not `#`, not backticks.** Verified sufficient for both observed
   defects. `_` must be preserved: the suite contains `def deliver_webhook` and
   `tests/test_http_headers.py`, where underscores are code, not emphasis. `#` and backticks are
   unnecessary because ordinary substring matching already tolerates them at phrase boundaries.
   Deliberate simplification; upgrade path is to add characters when a real failure demands one,
   never speculatively.
2. **Normalize symmetrically** — both the output and the phrase — so a signal author can write
   either `Status:` or `**Status:**` and get the same result.
3. **Fix the matcher before the scenario.** `3-all-complete` is the symptom that surfaced this;
   the matcher is the cause. Repairing the scenario first would leave the defect in place for the
   other four scenario files.
4. **Do not raise shot counts or relax thresholds.** That buries a real defect under statistics.
   It was statistical noise that nearly caused a correct line to be rewritten during the ponytail
   cycle.
5. **Expect the armed guard to produce real failures, and treat them as findings, not
   regressions.** Once `must_not_contain: "Status: Complete"` works, scenarios that have been
   passing may fail. That is the gate waking up.

---

## Verified file references

Verified against the working tree on 2026-08-15. Re-verify before editing.

| Reference | Content |
|---|---|
| `skill/eval/mechanical.py:30-36` | `must_contain` loop — raw `phrase in output` |
| `skill/eval/mechanical.py:38-44` | `must_not_contain` loop — raw `phrase not in output` |
| `skill/eval/mechanical.py:46-63` | `called_shot_required` — four literal field probes |
| `skill/tests/test_mechanical.py` | Existing fixture, 3 test classes, 13 tests — **add here, do not create a new file** |
| `skill/eval/scenarios/3_scenarios.json` | Carries both vacuous `Status: Complete` guards |
| `skill/eval/scenarios/2_scenarios.json` | `2-after-passing-test` — the four colon-terminated called-shot phrases |

---

## Preparatory refactoring

**None required.** `check_mechanical` is a 45-line pure function with a single entry point and an
existing deterministic test fixture. The three check loops are already separate. Structure is
ready as-is.

---

## Test list

Enumerated up front as a planning artifact; execution is one test at a time.

| # | Behavior | Currently |
|---|---|---|
| 1 | `must_not_contain` fires when the forbidden phrase is split by emphasis (`**Status:** Complete`) | passes — **the bug** |
| 2 | `must_contain` matches when emphasis sits outside the colon (`**Status**: Complete`) | fails — **the bug** |
| 3 | `called_shot_required` matches `**Test name**:` styling | fails |
| 4 | Underscored code identifiers are not mangled (`def deliver_webhook`) | passes — regression guard |
| 5 | Inline-code phrases still match (`` `bd update` ``) | passes — regression guard |
| 6 | Plain unformatted text behaves exactly as before | passes — regression guard |

Tests 4–6 are **green on arrival**. They are guards, not REDs. Label them honestly in commit
messages — the ponytail cycle established that a test written as a RED and found green must be
reported as such, not dressed up.

---

## Steps

Each step is one commit. **Stop for human review after each step** — do not batch.

| # | Type | Model | Step | Acceptance |
|---|---|---|---|---|
| 0 | prep | Sonnet 5 | Record the baseline: which scenarios currently pass, and the full 51-phrase signal inventory, into `eval/results/` or the plan file | Numbers written down before any matcher edit |
| 1 | `test:` **RED** | Sonnet 5 | Test list #1 in `tests/test_mechanical.py` — `must_not_contain: ["Status: Complete"]` against `"**Status:** Complete"` must fail the check | Expected failure, **one test**: the check currently reports `passed=True`; assertion expects `False` |
| 2 | `feat:` GREEN | Sonnet 5 | Add a module-level `_normalize(text)` stripping `*`; apply it in the `must_not_contain` loop only | Step-1 test passes; all 13 existing tests still green |
| 3 | `test:` **RED** | Sonnet 5 | Test list #2 — `must_contain: ["Status:"]` against `"**Status**: Complete"` | Expected failure, **one test** |
| 4 | `feat:` GREEN | Sonnet 5 | Apply `_normalize` in the `must_contain` loop | Step-3 test passes |
| 5 | `test:` **RED** | Sonnet 5 | Test list #3 — `called_shot_required` against a called shot written `**Test name**:` | Expected failure, **one test** |
| 6 | `feat:` GREEN | Sonnet 5 | Apply `_normalize` in the `called_shot_required` probe | Step-5 test passes |
| 7 | `test:` guard | Sonnet 5 | Test list #4–6 as regression guards, in one commit | Green on arrival — **say so in the commit message** |
| 8 | `fix:`/`docs:` **judgment** | Sonnet 5 | Re-run `TestPrompt3Evals` and `TestPrompt2Evals`. The `Status: Complete` guard is now armed in two scenarios. For each failure, decide: is the model genuinely rubber-stamping (finding — the prompt needs work), or is the scenario wrong? | A written verdict per failure. Do **not** silence a guard to get green |
| 9 | `fix:` scenario | Sonnet 5 | Repair `3-all-complete`: its input asserts completeness with no evidence for 5 of the Process Audit items, so declining to certify is the honest answer and the scenario punishes it. Add the missing evidence, or split the skeptical path into its own scenario | Interleaved A/B vs. the current scenario shows a materially better pass rate. Single runs prove nothing |
| 10 | `docs:` | Sonnet 5 | `skill/SUPERVISION-PROTOCOL.md`: record that prompt-change regressions are attributed by interleaved A/B, never a single run. `CHANGELOG.md`. Close #111 | Method note lands where the next session will find it |

### Full-cycle scope (per CLAUDE.md planning discipline)

Named explicitly rather than assumed:

- **Build system: no change required.** Verified — `skill/eval/` ships zero files in
  `pdca-framework.skill` (`unzip -l` returns 0 matches for `eval/`). `build-skill.sh` is untouched
  by this cycle. This line exists so CHECK can confirm the claim rather than infer it.
- **Documentation:** Step 10 covers `SUPERVISION-PROTOCOL.md` and `CHANGELOG.md`. No new command,
  so the CLAUDE.md commands table is unchanged — confirm at CHECK.
- **CHECK criteria:** see below.
- **ACT retrospective:** see below.

---

## Model selection

**Sonnet 5 for every step**, on the strength of the three supports below. The original tagging
put Steps 8–9 on Opus because they were specified as "use judgment." That was a smell: a step
whose spec is a disposition rather than a procedure is under-planned, whatever model runs it.

| Dimension | Rating | Note |
|---|---|---|
| Implementation complexity | Low | One 45-line pure function plus a helper |
| Pattern clarity | Clear | `tests/test_mechanical.py` supplies the idiom to copy |
| Context scope | Narrow | Two files for the entire matcher repair |
| Debugging likelihood | Low (0–7), Medium (8–9) | Deterministic units vs. live eval triage |
| External integration | None until Step 8 | No API key needed for the matcher repair at all |

**What makes Steps 8–9 safe for Sonnet:**

1. `skill/run-ab-eval.sh` (`910f647`) encodes the interleaved protocol and prints a Fisher
   p-value with an explicit instruction not to act on a null result. The statistical judgment is
   in the tool, not the operator.
2. The Step 8 triage table below replaces "decide whether the prompt or the scenario is wrong"
   with a lookup.
3. The verdict-before-fix rule below removes the temptation to skip straight to green.

**Residual risk that is not proceduralized:** Step 9 asks for a redesigned scenario input, which
is open-ended authoring. Its acceptance criterion is objective — the A/B must show improvement —
so a wrong answer is detectable rather than silently shipped, but **the human should read the
rewritten scenario text personally** rather than accept it on the strength of a passing gate.

### Step 8 triage table

For each scenario that fails once the `Status: Complete` guard is armed, apply in order:

| If the failing output… | Then | Action |
|---|---|---|
| Certifies completion while the scenario input states open items (TODOs, missing docs) | **Prompt finding** | Leave the scenario red. The CHECK prompt is not preventing rubber-stamping. Record it; fixing the prompt is a separate cycle |
| Certifies completion where the input contains no open items | **Scenario finding** | The guard is mis-specified for this scenario — it was never meant to fire here. Narrow the signal, and say so in the commit |
| Declines to certify, but is failing on a phrase the normalizer should have matched | **Normalizer gap** | A character beyond `*` is in play. Add it, with the failing string quoted in the commit message (see Decision #1) |
| Fails intermittently across ≥6 interleaved pairs with p ≥ 0.05 | **Noise** | Not a finding. Record the p-value and move on. Do **not** edit anything |

Anything that does not match a row is an escalation to the human, not an improvisation.

### Verdict-before-fix rule

The triage verdict lands as a **text-only commit** — plan file or CHANGELOG — *before* any commit
that edits a signal, scenario, or prompt in response to it. No commit may both diagnose and fix
the same failure.

This exists because the cheapest route to green is always to weaken the check, and that route
would restore the exact defect this cycle removes. Separating the two commits makes taking it a
visible, deliberate act rather than a quiet one.

## Risks

| Risk | Mitigation |
|---|---|
| Arming the guard turns currently-green scenarios red | That is the intended effect. Step 8 triages each on its merits; Decision #5 forbids silencing |
| Over-stripping mangles code identifiers | Decision #1 strips `*` only; test list #4 guards it |
| `2-first-step` carries `must_not_contain: "complete"` — a bare substring that also matches "completeness", "completed" | **Separate latent defect, out of scope.** File as a follow-up during ACT; do not fix inside this cycle |
| Eval re-runs in Steps 8–9 are noisy | `bash run-ab-eval.sh` — interleaved, Fisher-reported. Never attribute from a single run, and never from two sequential batches |
| API key availability | Steps 0–7 need none. Steps 8–9 do — do not start them without one, and do not defer them with a guessed cause the way Step 8 of the ponytail cycle did |

**Rollback:** every step is its own commit. Steps 1–7 touch only eval tooling, which ships to no
one.

---

## Definition of Done

- [ ] `cd skill && bash run-tests.sh` green (ruff + pytest)
- [ ] `"Status: Complete" in normalize("**Status:** Complete")` — the guard demonstrably fires
- [ ] Every newly-failing scenario has a written verdict, none silenced
- [ ] `3-all-complete` pass rate improved, demonstrated by interleaved A/B
- [ ] Docs updated (SUPERVISION-PROTOCOL, CHANGELOG); #111 closed
- [ ] Pushed; `git status` shows up to date with origin
- [ ] Human has signed off on CHECK and ACT

## CHECK step

Verify against this plan's acceptance criteria. Specifically confirm the build-system claim was
tested rather than assumed, that no guard was weakened to obtain green, and that every "green on
arrival" test is labelled as such rather than presented as a RED.

## ACT step

Retrospective (5–10 min). Specifically:

- Did stripping `*` alone hold, or did a real failure force more characters?
- How much of the historical eval flakiness did this actually explain? Compare post-fix pass rates
  against the 83% control figure recorded for `3-all-complete`.
- File the `must_not_contain: "complete"` substring trap as a follow-up.
- Carry forward the ponytail cycle's open ACT question: should plans state predicted failure causes
  at all? One did during that cycle, and it was wrong in a way that would have sent a less careful
  session rewriting correct code.

---

To execute each step, invoke **PDCA Do**. Do not begin any step without first opening that prompt.
