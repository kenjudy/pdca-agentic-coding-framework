# Implementation Plan: Repair Mechanical Signal Matching in the Eval Harness

> **Working artifact.** This file exists so the plan survives across sessions and threads.
> Delete it before merging to `main`.
>
> **Produced by:** PDCA PLAN phase (1a analysis + 1b plan), Opus 5, 2026-08-15
> **Origin:** ACT retrospective of the ponytail interop cycle. Filed as
> [#111](https://github.com/kenjudy/pdca-agentic-coding-framework/issues/111).
>
> **Progress:** Not started.

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
  changed. Two interleaved A/B pairs failed on *both* arms simultaneously.
- `TestPrompt2Evals` `2-after-passing-test`: GEval passed 3/3 while mechanical passed 1/3.
- Full signal inventory: 51 phrases across the 5 scenario files (see Step 0).

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
| 8 | `fix:`/`docs:` **judgment** | **Opus 5** | Re-run `TestPrompt3Evals` and `TestPrompt2Evals`. The `Status: Complete` guard is now armed in two scenarios. For each failure, decide: is the model genuinely rubber-stamping (finding — the prompt needs work), or is the scenario wrong? | A written verdict per failure. Do **not** silence a guard to get green |
| 9 | `fix:` scenario | **Opus 5** | Repair `3-all-complete`: its input asserts completeness with no evidence for 5 of the Process Audit items, so declining to certify is the honest answer and the scenario punishes it. Add the missing evidence, or split the skeptical path into its own scenario | Interleaved A/B vs. the current scenario shows a materially better pass rate. Single runs prove nothing |
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

| Steps | Model | Why |
|---|---|---|
| 0–7 | **Sonnet 5** | Low implementation complexity, clear established pattern, narrow context (2 files), deterministic tests, no API. `test_mechanical.py` supplies the idiom to copy. This is exactly the work Sonnet does well |
| 8–9 | **Opus 5** | Judgment, not implementation. Step 8 asks whether a newly-failing guard indicates a bad prompt or a bad scenario — a question about what the framework is *for*. Step 9 requires deciding what a defensible CHECK answer looks like when evidence is absent, then designing an experiment to prove the fix. The ponytail cycle showed both of these going wrong under an incorrect prior |
| 10 | Sonnet 5 | Mechanical documentation once the decisions in 8–9 are made |

Per the ponytail plan's model-switch note: prefer a **fresh thread per model** carrying this file,
rather than switching inside one thread — caches are model-scoped.

---

## Risks

| Risk | Mitigation |
|---|---|
| Arming the guard turns currently-green scenarios red | That is the intended effect. Step 8 triages each on its merits; Decision #5 forbids silencing |
| Over-stripping mangles code identifiers | Decision #1 strips `*` only; test list #4 guards it |
| `2-first-step` carries `must_not_contain: "complete"` — a bare substring that also matches "completeness", "completed" | **Separate latent defect, out of scope.** File as a follow-up during ACT; do not fix inside this cycle |
| Eval re-runs in Steps 8–9 are noisy | Interleaved A/B only. Never attribute from a single run |
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
