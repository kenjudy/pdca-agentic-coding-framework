# PDCA Framework Skill - Update Summary

## Unreleased

### Fixed: the stale-patch mechanism had silently deleted unrelated test coverage in 3 more files

- **The earlier "restore #156's lazy judge construction" fix only treated the one symptom
  CI caught. It should have been a full audit.** Re-applying `5680ce5`'s diff (computed
  between an old abandoned commit and the *old* `main` it was based on) onto *current*
  `main` doesn't just risk reverting one known fix — `git apply` matches on surrounding
  context lines, not semantics, so wherever a file had been modified by *other*, unrelated
  later work the old diff never saw, applying it silently deletes content that exists in
  current `main` but wasn't in the old diff's frame of reference. It reports success either
  way, and the full local suite stays green throughout, because deleting a *test* doesn't
  fail anything — it just makes coverage vanish.
- **Auditing every file the mechanism patch touched (`git diff <branch-base> -- <file>`,
  read in full, not just grepped for the one symptom already found) turned up two more
  instances**, both in files `5680ce5` also touched:
  - `tests/test_build.py` had lost 8 tests and an entire class
    (`TestDependencyFloors`) spanning four unrelated issues: #116/#170 (the "All done"
    guard), #127-129 (dependency floor guards), #155 (called-shot first-executing-
    assertion tests), and #138 (verify-before-claiming).
  - `tests/test_rubrics.py` had lost the entire `TestScoringBandsSpanTheThreshold` class
    from #153/#171 (band ordering, threshold placement, cross-rubric wording identity).
  - `.github/workflows/test.yml` had a comment reverted to a shorter, less informative
    pre-#156 version (functionally harmless — the actual no-key behavior was already
    covered by the restored guard test — but restored anyway since it's the exact
    explanation for the bug class this whole incident is about).
- **Fix: reset each corrupted file to the correct base (the actual commit this branch
  forked from, not the stale diff's original target) and re-applied only the genuinely
  new #148 content on top, verified this time by diffing the WHOLE file against the base
  and confirming zero unexplained deletions** — not just checking that my own new tests
  passed, which is what let two of these three slip through review earlier today.
- One incidental fix needed after restoring `TestScoringBandsSpanTheThreshold`: its
  band-ladder marker string (`"Then assign a score on a scale of 0 to 1:"`) no longer
  matched `GENERIC_TAIL`'s phrasing (`"...based only on the criteria listed above:"`).
  Loosened the marker to the stable prefix both share.
- 275 passed, 244 subtests — up from 261 before this audit, entirely restored coverage,
  no new production behavior.

### Fixed: 2-first-step truncated mid-response; 2-beads-ordering-capture lacked file locations

- Prompted by re-validating #148's band-reframing fix: two of five phase-2 scenarios still
  failed against the branch while passing against `main` at the same time. Reading the
  actual judge reasoning (not just the pass/fail count) showed two distinct, unrelated,
  non-rubric causes:
  - `2-first-step`'s response was cut off mid-sentence — the judge's own words: "cuts off
    mid-sentence... never reaching the required completion phrase." `eval/executor.py`'s
    `MAX_TOKENS = 2048` wasn't enough room for a called shot plus code across several
    tests plus the handoff phrase. Raised to 4096, pinned by
    `test_max_tokens_gives_room_for_a_multi_test_called_shot_walkthrough`.
  - `2-beads-ordering-capture`'s input never stated where `draft_step` or its tests live
    — unlike its sibling `2-first-step`, which explicitly says "File locations confirmed:
    ...". The model reasonably paused to ask, and was penalized for not proceeding.
    Added the same "File locations confirmed" convention to this scenario's input.
- Neither fix touches rubric prose — both are genuine harness/scenario-design gaps, found
  by reading *why* the judge failed the response rather than assuming the rubric was still
  at fault.

### Fixed: GENERIC_TAIL's bands scored correct refusals near zero (#148)

- **Dispatched 5 phase-scoped CI eval runs against the generic-tail rewrite (no
  scenario scoped yet) to check the rewrite itself didn't regress anything.** Phases
  1a, 1b, 3, 4 looked safe. Phase 2 — the exact rubric #136/#148's motivating example
  came from — showed all 5 GEval-scored scenarios flip from pass to fail, two with
  zero variance across 3 shots (not flaky noise).
- **Controlled the finding before trusting it.** The harness calls the API fresh
  every run, so a sequential comparison against the old tracked baseline can't
  distinguish "my rewrite caused this" from "the model just sampled worse this
  time" — exactly the uncontrolled-comparison risk `CLAUDE.md` already warns about
  for prompt changes. Dispatched a same-time-window control run of phase 2 against
  unmodified `main`. Result: `2-superpowers-branch-finish`'s correct refusal to
  merge before CHECK/ACT scored **0.90** under the old bespoke rubric at the same
  time my branch scored a similar correct-refusal response **0.00**. Model behavior
  was consistent; the judge's scoring under my new prompt was not — this is a
  rubric-wording effect, not sampling noise.
- **Root cause: `GENERIC_TAIL`'s bands were framed around positive demonstration**
  ("1.0 = every criterion listed above is fully met"), which reads as a checklist
  requiring every criterion to be affirmatively shown — with no room for a criterion
  that simply doesn't apply, like "called shot" when the scenario's correct behavior
  is refusing to write a test at all. The old bespoke bands were framed more
  holistically and left the judge room to reason that a response violates nothing
  even when it doesn't engage with most criteria.
- **Fix: reworded bands 1.0/0.7/0.4/0.0 around violation** ("no criterion listed
  above is violated"), matching the already-shipped, already-validated 0.6 band's
  own framing (#153) — the whole ladder is now internally consistent about what
  "compliant" means. Scope kept minimal: only the bands changed, not the
  Strengths/Weaknesses scaffold, which wasn't implicated by the evidence.
- Not yet re-validated against the judge — that's the next step before this can be
  considered mergeable.

### Fixed: reintroducing #148's mechanism from a stale patch reverted #156's fix

- **CI caught this one, not a local check.** Re-applying `5680ce5`'s diff (see the
  commit above) onto current `main` brought back eager, module-scope
  `AnthropicModel` construction in `tests/test_evals.py` (`JUDGE_MODEL =
  AnthropicModel(...)` at import time) — because that commit predates #156's fix for
  exactly this bug, and a plain diff has no way to know the target changed underneath
  it. The `eval-imports` CI job's collection-only step failed with `DeepEvalError:
  Anthropic API key is not configured`, correctly refusing to pretend a broken module
  was fine.
- **The same stale-diff application also deleted #156's own regression guards**
  (`test_judge_model_is_not_constructed_at_module_scope`,
  `test_eval_collection_needs_no_api_key`) from `tests/test_build.py`, since
  `5680ce5`'s version of that file predates them too. That is the more concerning half
  of this: the fast, local, no-API-key guard that exists specifically to catch this
  class of regression was silently removed by the same patch that reintroduced the
  bug it guards against, and the full local suite still reported green — only CI's
  separate network round-trip caught it, exactly the slow, expensive path #156 built
  the guard to avoid.
- Restored `judge_model()`'s lazy-construction pattern and both guard tests verbatim
  from `main`. Mutation-tested the restored
  `test_judge_model_is_not_constructed_at_module_scope` by reintroducing the exact
  eager-construction mistake and confirming it fails before re-fixing.
- **Lesson for future re-application of an old diff onto a moved target:** run the
  full local suite AND actually attempt the operation the old code was excluded from
  covering (here: collecting `tests/test_evals.py` with no `ANTHROPIC_API_KEY` set) —
  a diff that applies cleanly is not evidence it is still correct against everything
  that changed after it was written.

### Rubric scaffold and bands genericized so per-scenario scoping actually scopes (#148)

- **The mechanism above only fixed the numbered criteria list. Every rubric's scoring bands
  and Strengths/Weaknesses scaffold still narrated specific criteria by name** — "did it
  start with the happy path?", "stub implementation contains conditional logic" — so a
  scenario scoped away from a criterion in the numbered list was still judged against it
  invisibly, one section down. This is the exact defect that sank the first #148 phase-2
  attempt (`12ad72e`): "the mechanism worked and the feature did not."
- **Added `eval/rubrics/generic_tail.py`'s `GENERIC_TAIL`** — one shared scaffold-and-bands
  string, imported verbatim by all five rubrics, that never names a specific criterion or
  behavior; every reference is to "the criteria listed above". It scopes automatically with
  whatever `CRITERIA_ITEMS` subset a scenario selects, with no separate narrowing logic.
  Identical wording across all five rubrics is deliberate — the same principle #153 already
  established for the 0.6 band alone, generalized to the whole tail: rubric-specific phrasing
  here would itself be judge vocabulary, and #149 measured that backfiring twice already.
  Rubric-specific whole-response short-circuits (rubric_1a's vague-input exception, rubric_2's
  Process Police refusal exception) stay as a rubric-specific prefix before the shared text —
  they're overrides, not per-criterion narration.
- **rubric_2's dedicated "Stub Discipline" scaffold section was folded into the
  `stub-discipline` `CRITERIA_ITEMS` entry** rather than kept as a separate always-shown
  section, so its content is now properly scoped through the same mechanism as every other
  criterion instead of needing its own carve-out.
- **`test_scoped_criteria_leave_no_trace_in_bands_or_scaffold`** reproduces the exact prior
  failure: scoping rubric 2 to only `called-shot` and asserting "stub" and "happy path" don't
  appear anywhere in the assembled prompt, not just absent from the numbered list. Confirmed
  RED against the mechanism-only state (both concepts leaked via the hardcoded bands), GREEN
  after genericizing. `test_generic_tail_is_present_verbatim_in_every_rubric` guards the
  "identical across rubrics" property going forward — mutation-tested by inlining a
  rubric-specific tweak into one rubric's tail and confirming it's caught.
- **`tests/fixtures/rubric_criteria_snapshot.json` updated deliberately** — same rationale as
  #153: the byte-identity test it backs guards #148 phase-1's decomposition refactor, not
  rubric content for all time; this is an intentional content edit.
- **Not yet applied to any scenario, and not yet validated against the judge.** No scenario
  declares `geval_criteria` yet, so this ships as a structural capability. Unlike #153, this
  is not behavior-neutral for unscoped scenarios either — every rubric's scaffold and bands
  are now different prose than what shipped before, for every scenario in every phase, not
  just scoped ones. That needs real eval validation before this is considered done.

### Rubrics can score a scenario against only the criteria it claims (#148, mechanism)

- **Reintroduced `geval_criteria` scoping** (`eval/rubrics/assemble.py`, `eval/rubrics/__init__.py`,
  `eval/schema.py`), previously implemented in `5680ce5` and reverted in `12ad72e` — not because
  the mechanism was wrong, but because scoping the numbered criteria list left the scoring bands
  and Strengths/Weaknesses scaffold still narrating every criterion, so a "scoped" scenario was
  still evaluated on dimensions it never claimed. That prose-level gap is fixed separately below;
  this commit restores the mechanism unchanged and behavior-neutral (no scenario opts in yet, so
  every rubric renders identically to before).
- **Design constraints, unchanged from the original attempt, each backed by something measured
  rather than assumed:** out-of-scope criteria are omitted from the assembled text, never named
  as exclusions (#149 measured "do not penalise X" backfiring twice); selection follows the
  rubric's own declared order, not the caller's, so two scenarios naming the same subset in a
  different order still get the same prompt; numbering stays contiguous so the judge never sees
  a gap implying something was withheld; an unknown criterion id raises rather than silently
  resolving to "all" or "none"; narrowing requires a stated `geval_criteria_reason`, without
  which the field would be a nicer-looking `skip_geval` — a way to make a red scenario green by
  quietly dropping the criterion it fails.
- CI's `eval-imports` job collection-only check is restored alongside it, closing the same gap
  #156 found: `tests/test_evals.py` is excluded from the default suite, so a broken import there
  was previously only discoverable by dispatching a paid eval run.

### All five rubrics gain a scoring band anchored across the 0.5 threshold (#153)

- **Every rubric's bands jumped straight from 0.7 to 0.4, straddling `THRESHOLD = 0.5` with
  nothing between them.** A genuinely borderline response — one the judge considers neither
  "mostly compliant" nor "partially compliant" — had no band to land on, so a small judgment
  difference flipped pass/fail. The pre-fix #136 score distribution showed this directly: an
  empty 0.5–0.6 region, previously misread as judge instability rather than a structural gap
  in the ladder itself (corrected in #147).
- **This work already existed, unfinished, on a stale local branch (`claude/rubric-band-gap`,
  `10cc63f`) from a prior session — rediscovered only after independently re-implementing the
  same fix with bespoke, per-rubric band text and pushing it. That branch's design was better:
  wording is IDENTICAL across all five rubrics on purpose**, adding no phase-specific
  vocabulary a judge could over-index on — #149 measured naming a concept in a rubric making
  the judge score against it, twice, both times worsening scores. Five bespoke bands would
  have reintroduced exactly that risk. Discarded the bespoke version and adopted the identical
  wording instead: `0.6 — Borderline: every hard constraint for this phase is met, but the
  response has a soft weakness — it is verbose, leaves an edge case unraised, or its reasoning
  is sound yet thin. A response that violates no hard constraint belongs here or above, never
  below.`
- **Also adopted the prior branch's structural test** (`TestScoringBandsSpanTheThreshold` in
  `tests/test_rubrics.py`, replacing a weaker string-literal version written during
  reimplementation): it parses each rubric's score ladder and asserts a band strictly between
  0.4 and 0.7 *at or above that rubric's own threshold* — immune to a future rewording, and it
  catches a band placed below threshold (which would relabel the same failure rather than fix
  the gap), which a literal `"0.6 —"` match cannot.
- **Validated by reusing an already-spent full eval sweep from the prior branch** (GitHub
  Actions run `34510501344`, since the wording is now identical to what that run measured)
  rather than dispatching a redundant paid run: `4-short-session` — the scenario #153 itself
  names as the validation candidate — scored **0.60**, landing exactly in the previously-empty
  0.5–0.6 region. `4-tdd-breakdown` (already known-red, #151) stayed failing (2 of 3 shots at
  0.20) rather than flipping to pass, which is #153's own anti-masking check: a stably-failing
  scenario that starts passing would be evidence the band is masking real failures, not fixing
  a structural artifact.
- **`tests/fixtures/rubric_criteria_snapshot.json` updated deliberately.** The byte-identity
  test it backs (`test_assembled_criteria_is_byte_identical_to_the_published_string`) exists to
  prove #148's phase-1 decomposition changed no behavior — it is not a freeze on rubric content
  for all time. This change is an intentional content edit, so the snapshot was regenerated to
  match; the new structural test above is what guards this specific change going forward.
- **Adversarial critic pass (Opus) on the PR found the reused-evidence claim above was
  overstated: valid for phase 4, but not phase 2.** `2. Do/2. Test Drive the Change.md` and
  `eval/scenarios/2_scenarios.json` both changed after run `34510501344` was recorded (#155,
  #170), so that run's phase-2 numbers reflect a system prompt and scenario set that no longer
  exist. Closed the gap with a scoped, phase-2-only CI dispatch
  (`tests/test_evals.py::TestPrompt2Evals`, single pass) rather than assuming the reused
  evidence covered it. Result: `2-first-step` failed its GEval majority vote (1/3 shots passed:
  0.20, 0.30, 0.70) — but this is the *same* pre-existing "mechanical pass, GEval FAIL"
  divergence already visible in run `34510501344`'s own analyst notes, before #153 existed. No
  scenario flipped from a stable failure to a false pass; #153's anti-masking property holds for
  phase 2 too, on the scenario actually checked.
- **Two more critic findings, both fixed:** `TestScoringBandsSpanTheThreshold`'s existing tests
  call a band-extraction helper that sorts, so a band physically misplaced in the ladder (e.g.
  written after the 0.0 band instead of between 0.7 and 0.4) passed undetected — added
  `test_bands_appear_in_descending_order_as_written`, mutation-tested against exactly that
  misplacement. Nothing enforced the PR's own stated safety property (identical 0.6 wording
  across all five rubrics) — added `test_the_0_6_band_text_is_identical_across_all_rubrics`,
  mutation-tested against a one-word wording drift in one rubric.
- **Remaining critic findings filed rather than fixed inline:** #172 (eval validation evidence
  is ephemeral — GitHub Actions log retention is the only record, and no report captures which
  rubric-ladder version produced it) and #173 (the new band's "hard constraint" language is
  undefined in four of the five rubrics, checked empirically on phase 4 only). Also documented
  in `skill/eval/baselines/README.md`: the tracked baseline (`report_20260909_174245.md`)
  predates #153, so a future GEval comparison against it needs the same care as a
  dependency-version mismatch.

### Called shot must predict the first-executing assertion, not the most meaningful one

- **The DO master's CALLED SHOT block named "the exact assertion message or error expected" with
  no anchor to *which* assertion, when a test carries several (#155).** In practice the prediction
  drifts to the assertion that best expresses the behavior, while the test runner reports the
  first one that executes. When those differ, a correct test's RED reads as a misprediction and
  the STOP rule fires for the wrong reason — or worse, trains the operator to wave the mismatch
  through, eroding the rule for the case it exists to catch. `Expected failure:` now asks purely
  for the assertion expected to fail first; the remedy (reorder the assertions or split the test)
  moved out of the bracket and into the STOP sentence itself, next to the ordering guidance it's
  paired with.
- **`Testing Anti-Patterns.md` gains item 9, "Loose Called Shot,"** naming the pattern so it is
  citable in retros the way item 8 has been used as diagnostic vocabulary all cycle rather than
  re-explained from scratch each time. Matches item 8's own layout: `---` separator, a Quick Check
  line, and a cross-reference from the DO master at the point the guidance applies.
- **`Human Working Agreements.md` gains the matching intervention question** — "Which assertion
  did you predict, and which one fired?" — alongside the section's existing TDD-discipline
  questions.
- **Caught by an adversarial critic pass, per this cycle's own CHECK requirement: the first version
  stated a false universal.** "The test runner stops and reports at the first failing assertion"
  is true for fail-fast styles and false for styles that intentionally aggregate multiple
  assertions per test — `unittest.subTest`, soft assertions, `pytest-check`, RSpec's
  `aggregate_failures`. Under those, a legitimate RED report names several assertions together, and
  "a RED on any other assertion is a misprediction" would falsely STOP the model — reintroducing,
  for a different framework family, the exact bug #155 was filed to eliminate. Not hypothetical:
  `skill/tests/test_build.py` uses `subTest` in several places written this same cycle. Both the DO
  master and item 9 now qualify for aggregating styles: check whether the predicted assertion is
  among those reported, not whether it ran first. The test that pinned item 9's heading alone
  (passing against an empty section) was also caught the same way and now pins the Rule paragraph;
  mutation-tested afterward to confirm it no longer passes vacuously.
- **Not verifiable by the eval harness, and said so rather than hidden.** The harness is
  single-turn and never executes real code — the same structural limit #136 already found for
  "Run the test." Whether a model predicted the actual first-executing assertion can only be
  observed in real TDD work, not a synthetic scenario, so `rubric_2.py` and the scenario JSON are
  deliberately untouched. Confirmed instead that the four labels `called_shot_required` matches on
  (`Test name:`, `Behavior under test:`, `Expected failure:`, `Why this test first:`) are unchanged
  — this edit only touches bracket-instruction text and the follow-up sentence, so the mechanical
  tier's behavior across every scenario that uses it is unaffected.

### The "all done" guard now catches sentence-initial capitalization (#116)

- **`must_not_contain: ["all done"]` matched case-sensitively, so the most natural phrasing —
  sentence-initial "All done" — evaded it entirely.** Demonstrated live in #116, and after #112
  this became `2-first-step`'s *only* mechanical signal.
- **First attempt case-folded `must_not_contain` globally in `eval/mechanical.py`. An adversarial
  critic pass (operator-chosen model: Opus) found it broke two other scenarios on the same
  branch.** `1a-vague-goal`'s `"Add an index"` and `4-tdd-breakdown`'s `"you should"` both rely on
  capitalization to distinguish a directive statement from an incidental, compliant mention —
  folding the whole signal type made both start matching lowercase prose they were never meant to
  catch. Confirmed empirically: a compliant 1a response containing "...tell you to add an
  index..." passed against `main` and failed against the folded version; likewise a compliant ACT
  response containing "You should have the final call..." Reverted the code change entirely
  (`eval/mechanical.py` and `tests/test_mechanical.py` are now byte-identical to `main`).
- **Fixed at the data layer instead:** added the capitalized variant `"All done"` directly to the
  three scenarios that actually need it (`2-first-step`, `2-beads-ordering-capture`,
  `2-ponytail-precedence`) in `eval/scenarios/2_scenarios.json`, leaving every other
  `must_not_contain` phrase's case-sensitivity untouched.
  `test_all_done_guard_catches_sentence_initial_capitalization` in `tests/test_build.py` pins the
  fix against the real scenario data (RED confirmed before the data edit, GREEN after), and the
  two previously-broken compliant responses were re-verified to pass clean against the final
  scenario file.

### run-evals.sh now offers to promote a full sweep to the tracked baseline

- **Promotion into `eval/baselines/` was entirely manual since #152 created the directory** —
  documented only in `baselines/README.md`, prompted by nothing. Every full sweep since,
  including the one that validated #153's band-gap fix, was read once and left in
  `eval/results/`, gitignored, gone. #157's cross-run pooling needs an accumulating corpus and
  has had nothing to pool over as a direct result.
- **`promote_baseline.py` (#159)** offers to promote a full sweep after `run-evals.sh` finishes,
  showing the `eval.aggregate` divergence summary against the existing baseline before asking.
  Three properties, each closing a specific way this could go wrong: it **never blocks in a
  non-interactive context** — `evals.yml` dispatches this script on a GitHub Actions runner with
  no TTY on stdin, and a blocking prompt there would hang the job rather than fail loudly, the
  opposite of #141/#142/#156's fixes this cycle; a **partial report is never promotable**,
  regardless of interactivity or answer, decided from the report's own content (does it score
  every scenario?) rather than trusted from `run-evals.sh`'s argument count, so a bug in the
  shell-side gate cannot corrupt `test_baseline_exists_for_every_scenario`'s completeness
  invariant; and it **only offers, never auto-promotes**.
- Verified past the unit tests: a real, non-mocked shell invocation in this same non-interactive
  environment confirmed both the full-sweep and partial-report paths exit `0` with no hang.
  `typecheck.sh`'s own `test_ci_mypy_covers_every_top_level_module` caught that the new script
  wasn't in mypy's hardcoded module list — the exact class of drift it was built in #114/#126/#141
  to prevent, working as intended on the first new script since.

### Working agreements now require verifying a prior command's result before claiming it

- **`Human Working Agreements.md` gains item 11, "VERIFY BEFORE CLAIMING" (#138).** Item 4 already
  required verifying test expectations; nothing generalized that discipline to CLI/tool
  orchestration. Concrete incident: a `bd update --append-notes` heredoc failed with a bash syntax
  error, the three commands in the invocation weren't `&&`-chained, so execution continued past the
  failure into two `bd close` calls whose `--reason` text claimed the notes had been recorded —
  they had not. Caught only by later re-running `bd show` against the claim rather than trusting
  it. `test_working_agreements_requires_verifying_a_prior_commands_result` pins the new item in
  the default suite, checked against the master source directly so it runs with no build step.

### Dependency floors raised to match what is already locked

- **`anthropic`, `deepeval`, `ruff` floors in `pyproject.toml` had drifted behind `uv.lock`.**
  An earlier batch relock resolved `anthropic 1.4.0`, `deepeval 4.2.2`, `ruff 0.16.6`, but the
  declared floors in `[project.optional-dependencies]` were never raised to match — left at
  `>=1.0.0`, `>=4.1.10`, `>=0.16.4`. Real gap, not stale noise: an install without the lock
  (or an older compatible resolution) could silently receive versions below what this project
  actually builds and tests against. Dependabot's #127, #128 and #129 correctly reported it;
  raised the three floors to exactly what's locked, closing all three.
- **`test_declared_floor_matches_the_locked_version`** guards the invariant going forward —
  generalized to every declared floor, not hardcoded to these three packages. Deliberately
  asserts equality, not `floor <= locked`: the latter is a tautology as long as `uv.lock`
  resolves at all (`uv lock` guarantees the resolved graph satisfies the declared constraint),
  so it would have passed with this exact gap still wide open. Equality matches the project's
  own stated convention ("Floors raised and the lockfile relocked in one pass") — confirmed
  against every other floor before relying on it: `pytest`, `python-dotenv`, and `mypy` already
  satisfied it; `anthropic`, `deepeval`, `ruff` were exactly the three that didn't.

### Check phase now requires an operator-chosen critic pass

- Following a downstream retrospective (see the #144 Documentation entry below): anti-pattern
  #8 (Partial-Instance Coverage) recurred twice more on the very next cycle after it was
  written, both caught only by a fresh adversarial critic reading the whole file/change --
  not by re-reading the anti-pattern list. Advisory text does not self-apply.
- The Check phase's Decision probe (`claude-addon/injections/check-review-probe.md`) now
  requires an adversarial critic pass with a fresh subagent for any change spanning more than
  one file, or any acceptance criteria with an end-to-end/completeness claim -- with the
  operator choosing which model runs the critique, rather than the session defaulting
  silently or reviewing its own work.
- `check-prompts.md`'s Process Audit checklist item is updated to match: a self-review or
  re-read by the same session that did the work is explicitly named as not a substitute.
- `testing-anti-patterns.md` #8 gains a short addendum documenting the recurrence itself, so
  the anti-pattern's own text carries the evidence for why the critic pass is now required
  rather than optional.

### Documentation (#144)

- Added anti-pattern #8 (Partial-Instance Coverage) to `testing-anti-patterns.md`: testing
  the first edited instance of a repeated assumption (one step of a multi-step flow, one
  file of a documented multi-file change) and closing the task, when the acceptance
  criteria makes a whole-flow or whole-file claim. Found via a retrospective on a downstream
  project where two fixes each passed their own tests but left the stated end-to-end claim
  untested as a whole -- caught only by a fresh adversarial critic reading the whole
  file/flow, not by Do-phase tests or the Check phase that followed.
- Added matching checklist lines: `do-prompts.md`'s "Ready for commit?" and
  `check-prompts.md`'s "Process Audit" both now point back to anti-pattern #8.

### Dependency Updates

- **`aiohttp` 3.13.3 → 3.14.3** — a transitive dependency via `deepeval`, not declared directly
  in `pyproject.toml`. Reported in #137 as CVE-2026-34520 (malformed HTTP response header
  parsing in the C parser). The issue's suggested patch hand-edited the version string in
  `uv.lock` while leaving the old wheel hashes in place, which would have made `uv sync --locked`
  fail in CI rather than fix anything. Re-resolved instead with
  `uv lock --upgrade-package aiohttp`; only aiohttp's own package block changed — confirmed by
  diffing every `name =`/`version =` pair in the lock before and after.

- Floors raised and the lockfile relocked in one pass, superseding four separate dependabot
  PRs (#127, #128, #129, #130): `anthropic >=1.0.0` (resolved 1.4.0, up from 0.122.0),
  `deepeval >=4.1.10` (4.2.2), `ruff >=0.16.4` (0.16.6), `mypy >=2.3.1` (2.3.1, already
  satisfied). Batched deliberately: each PR bumps a floor in
  `[project.optional-dependencies]` without touching `uv.lock`, so each would fail CI under
  `uv run --locked` on its own, and merging them one at a time would conflict on the lock.
- **`anthropic` crossed a major version**, which is the risk #122 was filed for.
  `tests/test_eval_imports.py` — added for exactly this — passes against 1.4.0: the client
  class, `AnthropicModel`, `GEval`, `LLMTestCase` and the rubric modules all still construct.
  That covers the API surface, not scoring behaviour.
- setuptools `>=83.0.0` → `>=84.0.0`.

### Bug Fixes

- **`2-superpowers-tdd-precedence` no longer runs GEval (#136).** Three 10-shot runs measured
  the Phase 2 judge scoring the same behaviour anywhere from **0.00 to 0.90**, docking it for
  test ordering and for not executing tests — neither claimed by the scenario, and the latter
  impossible in a single-turn harness with no shell or test runner. Two attempts to state that
  in the rubric were measured and **reverted**: telling an LLM judge "do not penalise X" made X
  salient and it penalised harder, with the file-reading clause inverted outright into *"Step 4
  requires… avoiding requesting file reads"*. What the scenario actually claims — that the
  called shot survives when superpowers' TDD skill is active — is verified by the mechanical
  tier, which held at 17/18, 22/23 and 17/18 across those same runs while GEval swung wildly.
  Turning GEval off keeps the signal and drops the noise. The fault stays visible rather than
  hidden: #147's divergence note reports mechanical/GEval disagreement in the report itself, and
  #148 tracks the root cause. `test_skip_geval_scenarios_still_assert_something` now blocks the
  obvious abuse — a scenario with GEval off and no mechanical signal cannot fail, and would
  report as a pass forever.

- **`tests/test_evals.py` no longer needs an API key to import (#156).** It built
  `AnthropicModel` at module scope, and deepeval raises during construction when no key is
  configured — so the file could not be imported, collected, or meaningfully type-checked
  without a credential. That is why it slipped past every cheap check the project has, and why
  every edit to it has been unverifiable except by dispatching a paid eval run. The judge is
  now built on first use, cached, so it is still constructed exactly once per session at the
  point an API call is about to happen — mirroring `eval/executor.py`'s `_client()`, which
  defers construction for the same reason.
- **The CI collection step now runs with no key at all**, which is what proves the property
  holds. It previously passed a dummy key as a workaround; leaving that in place would have let
  module-scope construction return unnoticed, since the step would have kept passing.
  `test_judge_model_is_not_constructed_at_module_scope` checks the source by parsing it rather
  than importing it — importing is the thing that did not work, and the guard has to run in the
  default suite, which installs neither deepeval nor a key.

- **Verdicts can now be pooled across runs (#147 deliverable 2).** `eval/aggregate.py` reads
  several reports and names the scenarios whose **verdict changed** between them — the question
  that decides whether a scenario is usable as a regression gate, and one no single run can
  answer. Analyst Notes sees variance within one run; the divergence note sees the two tiers
  disagreeing in one run; neither could see a scenario passing on Monday and failing on Tuesday.
  The reporter cannot either: its fixture is `scope="session"`, so each `run-evals.sh`
  invocation writes its own file, and `evals.yml`'s multi-shot dispatch was producing exactly
  this data and dropping it.
- **It reports no cause, deliberately.** #147 as filed proposed flagging bimodal scores as
  "judge instability"; that was corrected, because every rubric's bands are `1.0/0.7/0.4/0.0`
  against a `0.50` threshold (#153), so a gap at the threshold is partly structural and a shape
  alone cannot separate an unstable judge from an unstable model. Naming a cause would be #141's
  defect one level up — output that reads like a measurement. It refuses to run on a single
  report for the same reason: "stable" is not a conclusion one observation supports.
- Verified against the two real full sweeps to date, where it independently reproduced the one
  verdict flip previously found by hand: `2-first-step`, 1 pass / 1 fail, scores 0.30–0.70.

- **CI now collects `tests/test_evals.py` without running it.** That file is excluded from the
  default suite because it makes real API calls, so a broken import there was previously only
  discoverable by paying for an eval run. It also cannot be imported without a credential — it
  builds `AnthropicModel` at module import time — which is why every cheap check had skipped it.
  The step passes a deliberately fake key and executes nothing.

- **Rubric criteria are now addressable (#148, phase 1).** Each rubric exposed one monolithic
  `CRITERIA` string, so `_rubric_for_prompt(prompt_id)` handed every scenario in a phase the
  same criteria — including ones the scenario never claimed to measure. That produced measured
  mis-scoring in rubric 2 (#136), rubric 3 (#111) and rubric 4 (#151), and `skip_geval`, the
  only lever for silencing it, is all-or-nothing. The five rubrics now expose `CRITERIA_ITEMS`
  — 26 stable identifiers across the set — assembled by `eval/rubrics/assemble.py`.
- **This phase is provably behaviour-neutral.** `test_assembled_criteria_is_byte_identical_to_
  the_published_string` pins every assembled rubric against a snapshot of the text that shipped
  before decomposition, so no API spend can be required to show the judge reads the same prompt.
  That property is the point: any score movement from the per-scenario selection landing later
  is attributable to scoping alone, not to rewording. Out-of-scope criteria will be **omitted**
  from the assembled text rather than named — #149 measured the alternative twice, and a "do not
  penalise X" clause reliably becomes "penalise X".

- **The repo has a tracked eval baseline for the first time (#122).** `skill/eval/baselines/`
  now holds a full 21-scenario sweep run at `deepeval 4.2.2` / `anthropic 1.4.0`, recorded in
  the report itself by #145's provenance line — making it the first eval run in the project's
  history that can be attributed to a dependency set. 20 of 21 scenarios pass;
  `4-tdd-breakdown` is a known red tracked in #151 and is labelled as such, so a future
  comparison can tell it from a regression. `test_baseline_exists_for_every_scenario` requires
  every scenario in `eval/scenarios/` to appear in some baseline, so adding a scenario without
  baselining it now fails the suite.
- **#147's divergence note found a new instance on its first full sweep.** It flagged
  `4-tdd-breakdown` — mechanical passing, GEval failing — in rubric 4, which nobody had
  examined. That is the third rubric implicated in #148's root cause, after rubric 2 (#136)
  and rubric 3 (#111).

- **Two instruction files told readers to get baseline scores from a directory git has never
  tracked (#122).** `CLAUDE.md`'s Validating Prompt Changes step 1 and
  `SUPERVISION-PROTOCOL.md`'s "Establish a Baseline" both pointed at `skill/eval/results/`,
  which is gitignored (`.gitignore:28`) and whose `git log --all` is empty. Both instructions
  have therefore been inoperable on every fresh clone and in CI for as long as they have
  existed — and #122's own closing procedure, "compare against the baselines in
  `skill/eval/results/`", had no left-hand side. New tracked `skill/eval/baselines/` holds
  deliberately promoted reports; `results/` is deliberately **not** un-ignored, because every
  run writes a fresh timestamped report there and tracking it would dirty the tree after each
  run — the churn pattern `uv.lock` already produced.
- `test_baselines_dir_is_not_gitignored` runs `git check-ignore` and fails if anyone adds the
  new directory to `.gitignore`, which would reproduce the defect silently while both
  instructions carried on reading as though they worked.

- **The Phase 2 judge could dock the bare word "complete", which #112 had already fixed in the
  mechanical tier.** #112 removed the stem from `must_not_contain` because it matched the ordinary
  adjective — *"here's the complete sequence"* is the behaviour the prompt asks for. Criterion #5
  and band 0.0 still quoted `"complete" or "done"` verbatim, so the same false positive survived
  one tier up. Both now describe the behaviour — declaring the work itself finished rather than
  handing off to CHECK — instead of naming words. Unmeasured against the judge: found by reading
  the rubric, not by a failing shot.

- **A dead eval harness could not be told apart from a failing scenario.** A shot that
  dies before reaching the API — missing build artifact, absent key, network failure —
  produces no scored result, but pytest exits non-zero either way, so a caller counting
  exit codes reported a crash and a genuine failure identically. This was not
  hypothetical: the first eval run of #131's Step 0 reported `5 shot(s); 5 did not pass`
  from a harness that never called the API once, and it read exactly like a confirmed
  hypothesis. `eval/README.md`'s thesis is that a broken eval is self-sealing, since the
  eval *is* the mechanism meant to notice.
- **`skill/check_eval_ran.py`** distinguishes them. The evidence was already in the
  reports — a crashed shot leaves a Summary table with a header, a separator and no data
  rows — so the check is a pure function over report text, needing no API key, no network
  and no live run. That is deliberate: it has to work in exactly the conditions where the
  harness cannot. `run-evals.sh` now exits **2** when nothing was measured, distinct from
  **1** for a real scenario failure, and scopes the check to reports from the current run
  so an earlier scored report cannot mask a run that scored nothing.
- **`evals.yml` counts the two separately** and fails loudly on a harness error rather
  than folding it into a "did not pass" tally.

- **The pre-commit mypy hook had never been able to run on any machine but one.**
  `.claude/settings.json` is checked in, and its `PreToolUse` hook `cd`-ed to an absolute
  path under one contributor's home directory. Everywhere else the `cd` failed, the `&&`
  chain short-circuited, and the trailing `exit 0` reported success — an advisory gate
  that looked configured to everyone and could fire for no one. Found during a review of
  #139, and a better instance of that PR's own subject than the PR contained.
- **`skill/typecheck.sh` is now the single mypy invocation**, called by both CI and the
  hook. They previously held separate argument lists and had already diverged: the hook
  named `eval tests/test_build.py` while CI named six targets. That is #114 in miniature —
  two copies of one procedure drifting silently because only one of them ever ran.
- The hook now resolves the repository from `CLAUDE_PROJECT_DIR`, falling back to
  `git rev-parse`, and **reports explicitly when it cannot locate the script** rather than
  skipping in silence. `test_settings_json_has_no_machine_specific_path` asserts no
  home-directory path returns.

- **`CLAUDE.md` and `AGENTS.md` gave opposite instructions on pushing.** Both are
  auto-loaded agent instruction files — `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex
  — and on the most consequential action either agent takes they disagreed outright:
  `CLAUDE.md` said *"NEVER say 'ready to push when you are' — push yourself"*, while
  `AGENTS.md` said *"Do NOT push without explicit human instruction"*. Nothing could detect
  the divergence, since each file is only ever read by the agent it governs.
- Both now state the same policy: **the operator approves the push in a human-in-the-loop
  session, and an agent pushes on its own initiative only when explicitly instructed to act
  autonomously.** `CLAUDE.md`'s Session Completion sequence gains an approval step;
  `AGENTS.md` gains the autonomous carve-out it lacked.
- `test_push_policy_is_consistent_across_agent_files` asserts both halves appear in both
  files, so dropping either one — or reintroducing an unconditional self-push instruction —
  now fails the suite.
- **`run-evals.sh` never built the skill or synced the eval extra.** The harness reads the
  built prompt files under `pdca-framework/references/`, which are gitignored artifacts. On
  any tree without a prior build every scenario died with `FileNotFoundError` on
  `do-prompts.md` before reaching the API — and each dead shot was reported as "did not
  pass", indistinguishable in a summary count from the model actually failing the scenario.
  A harness that cannot run must not read like a harness delivering a verdict. Same shape
  as #89, in the script next door.
- **Eval reports are now echoed into the CI job log**, not only uploaded as an artifact.
  Artifact download is authenticated, so for any consumer that cannot reach one the shot
  count was the sole readable output — precisely the number `eval/README.md` says never to
  trust alone.

### Optional superpowers interop (#131)

- The pdca-framework skill now offers optional interoperation with
  [superpowers](https://github.com/obra/superpowers) (MIT, © Jesse Vincent), a skills
  library for coding agents. Two references — `references/superpowers-setup.md` and
  `references/superpowers-workflow.md` — surfaced via a "Superpowers Integration (Optional)"
  section in `SKILL.md`.
- **Unlike beads and ponytail, superpowers is not something PDCA invokes.** It installs a
  `SessionStart` hook that injects its dispatcher into every session, and the dispatcher
  states that using an applicable skill is not optional. There is no supported partial
  install. So the addon does not try to control whether superpowers is active; it rests on
  one precedence rule, which is superpowers' own published clause: user instructions take
  precedence over skills. PDCA governs when work is verified and finished; superpowers
  governs how individual tasks are carried out.
- **The addon's main content is a use/decline map**, not a rulebook: which skills fill real
  PDCA gaps (`systematic-debugging`, `using-git-worktrees`, both code-review skills,
  `dispatching-parallel-agents`, `writing-skills`) and which overlap a phase and therefore
  defer to the prompt in front of you.
- **No phase master was changed, because measurement said none needed changing.** Three
  conflicts were hypothesised and each was measured against the *unmodified* masters at five
  shots: that `finishing-a-development-branch`'s merge menu would end a branch without ACT
  (refuted — every response refused the merge, scoring 0.90–1.00 against a 0.50 threshold),
  that superpowers' TDD skill would drop the called shot (inconclusive — mean 0.6, stddev
  0.36, flagged flaky by the harness itself), and that `verification-before-completion`
  would be mistaken for CHECK (refuted — the model declined to certify and named both
  planted gaps). Guard clauses for conflicts that do not occur would have added text to
  three places to prevent nothing.
- **Nothing upstream is vendored** and no hooks or settings files are written. A copied
  snapshot of third-party skills would diverge silently from its source, which is #114 in a
  new costume.
- Cost to users without superpowers installed, measured: `SKILL.md` grows 917 bytes. Every
  other packaged file — all four phase prompts, working agreements, testing anti-patterns,
  and all eight existing addon references — is byte-for-byte unchanged. The two new files
  ship in the package but are never loaded unless requested.

### Build and Distribution

- **The release workflow could never publish.** `release.yml` declared no `permissions:`
  block, so `GITHUB_TOKEN` fell back to the repository default (read-only) and
  `softprops/action-gh-release` failed with `403 Resource not accessible by integration`.
  Every release run in this repository's history — v1.0.1 through v1.3.0 — finished with
  conclusion `failure` for this reason, and each release was published by hand instead, so
  the red workflow blocked nothing and there was no occasion to read the log. Now grants
  `contents: write`, with `test_release_workflow_grants_contents_write` asserting both the
  block and the scope.

### New Tooling

- **`.github/workflows/evals.yml`** — manually-dispatched workflow for running prompt
  evals in CI, so `ANTHROPIC_API_KEY` stays in GitHub secrets rather than reaching a
  terminal, a `.env` file, or an agent session. `workflow_dispatch` only; the test suite
  asserts no automatic trigger exists, since a full run costs roughly $2–5. Takes a
  `test_id` (required, no default, so scope is always deliberate) and a `shots` count —
  the latter because a single run cannot attribute a failure to a prompt change:
  `3-all-complete` was measured failing 3 of 18 runs against an unmodified master.

- **`skill/check_changelog.py`** — enforces `CONTRIBUTING.md`'s per-PR CHANGELOG rule,
  which had no mechanism behind it and was routinely missed. Runs on pull requests only,
  because the check needs a diff; a unit test could at most assert that some `##
  Unreleased` section exists, which stays true forever after one entry and is blind to the
  PR that forgot. Dependabot is exempt — its bumps are summarised once at release time.

- **Eval reports now flag when the two scoring tiers disagree (#147).** The mechanical tier
  confirms required strings are literally present; GEval judges semantically. When mechanical
  passes and GEval fails — or the reverse — the judge scored something the rubric may not
  declare, which is the fingerprint of a rubric fault rather than a scenario failure. Analyst
  Notes previously flagged only variance (`stddev > 0.2`), and variance is the symptom *both*
  candidate causes share, so it could never separate a flaky model from a flaky rubric. That
  gap is what left #136 undiagnosed until a dispatched 10-shot run and a human reading
  responses; the divergence there was 17/18 mechanical passes against 13/18 GEval failures,
  both already printed on the same summary rows and never compared. The note is phrased as a
  hypothesis pointing at specific recorded responses, not a verdict — a note that reads as a
  finding would be #141's defect one level up. Costs nothing: no API calls, no extra run.

- **Eval reports now record the dependency versions that produced them.** Every report
  gains an `**Environment:**` line naming the installed `deepeval` and `anthropic`
  versions, read via `importlib.metadata` so the reporter stays importable without the
  eval extra. Reports previously carried a timestamp and nothing else, which is why #122
  — did the `deepeval` 3.9.9 → 4.x bump change how scenarios score? — turned out to be
  unanswerable in retrospect: no run on record could be attributed to a version, so there
  was no before-state to compare against. This is what makes the *next* major bump
  answerable without anyone remembering to write it down. `tests/test_evals_reporter.py`
  now also runs in CI's `eval-imports` job: the default suite installs neither package, so
  there the provenance assertions only ever exercise the "not installed" branch, and the
  path that produces the string a human actually reads would run nowhere.

## v1.3.0 (2026-08-18)

> **Windows builders:** `build-skill.ps1` now requires a Python 3 interpreter on `PATH` as
> `python3` or `python`. It is a thin wrapper over `build.py` and no longer carries its own
> PowerShell implementation of the build. The published `.skill` package is unaffected — this
> matters only if you build from source on Windows.

### Build system — shared `build.py` extraction (#114)

- **Fixed silent drift between the two build scripts.** `build-skill.ps1` still targeted
  `skill/src`, a directory renamed to `skill/pdca-framework` long ago: it shipped 7 of 16 files at
  the wrong ZIP root, with raw `CLAUDE_INJECT` markers unreplaced and license/attribution blocks
  unstripped in 5 files, and it created an untracked `skill/src/` on every Windows build. Nothing
  caught it because nothing ever ran it — there was no test that executed `build-skill.ps1`.
- **Extracted the build into `skill/build.py`**, a single stdlib-only implementation. Both
  `build-skill.sh` and `build-skill.ps1` are now thin wrappers that locate a Python interpreter
  and call `build(skill_dir) -> Path`; neither carries composition, license-stripping, injection,
  or packaging logic of its own, so the two platforms can no longer diverge — there is only one
  place a fix or a mistake can happen.
- **Added `tests/test_builder.py::test_powershell_build_matches_bash`**, a parity test that runs
  both `build-skill.sh` and `build-skill.ps1` from a clean tree and asserts the resulting packages
  have identical member names and per-member SHA-256 hashes. Both builds now force a from-scratch
  state before comparison — `build.py` writes generated files via `write_text()`, which truncates
  an existing file in place but leaves its mode untouched, so a build that reuses a tree left over
  from an earlier build can inherit that build's file permissions and mask a defect in the current
  one. This is not hypothetical: the packaged-executable-bit test (`test_export_script_is_executable`)
  passed on its first draft for exactly this reason, before `build.py` actually set the permission
  bit itself. `BUILD.md` documents this as "Stale-artifact masking."
- **CI now hard-fails rather than skips the parity test when `pwsh` is missing.** A silently
  skipped parity test is indistinguishable from a passing one in pytest's summary line — exactly
  the blind spot that let the original drift go undetected — so under `CI=true` a missing `pwsh`
  is treated as a test failure, not a skip. Locally, without `CI=true`, the test still skips
  gracefully for contributors without PowerShell installed.
- `mypy` coverage widened from `eval tests` to `eval tests build.py` so the new module is
  type-checked in CI.

### Dependencies — lockfile corrected and pinned (#113)

- **`skill/uv.lock` could not satisfy `skill/pyproject.toml`.** Five declared floors were
  violated at once: `anthropic` 0.99.0 against `>=0.120.2`, `deepeval` 3.9.9 against `>=4.1.4`,
  `mypy` 1.20.2 against `>=2.3.0`, `pytest` 9.0.3 against `>=9.1.1`, and `ruff` 0.15.12 against
  `>=0.16.0`. Every `uv run` therefore re-resolved and rewrote the lockfile, leaving a ~450-line
  dependency diff in the working tree of anyone who ran the test suite — and a routine
  `git commit -a` would sweep a dependency upgrade into an unrelated change.
- Relocked deliberately as its own commit, and `run-tests.sh` now uses `uv run --locked` so
  future drift is a hard failure rather than a silent rewrite. Deliberately *not* `--frozen`,
  which stops the churn by skipping the staleness check entirely — that would have hidden the
  condition permanently instead of fixing it.

### Repository hygiene — gates that could not fail

Several checks in this repo reported green without ever having been capable of failing. Each is
now backed by a mechanism:

- **`run-tests.sh` never provisioned its own venv (#89).** It called `uv run` and relied on
  something else having synced the extras — which both CI workflows do, which is why the script
  was never observed running unprovisioned. On a fresh clone it fails with `No module named
  pytest`; worse, where an ambient `ruff` exists on `PATH` the lint gate reports green while
  running a version *below* the floor `pyproject.toml` declares. The script now syncs
  `--extra test --extra lint` itself, so local and CI runs provision identically.
- **The release checklist's "update `skill/README.md`" step had nothing behind it.** It was
  skipped at v1.2.0 and nothing failed. `TestReadme::test_current_version_matches_changelog` now
  ties the README's version to the newest released `CHANGELOG.md` heading.
- **A matching README and CHANGELOG can still disagree with the tag**, and no unit test can see
  a tag. `skill/check_release_version.py` runs in the release workflow against
  `github.ref_name` and reports every disagreement between the tag and both files in one pass.
- **Nothing exercised the eval harness's third-party surface (#122).** `eval/executor.py`
  imports `anthropic` lazily and `tests/test_evals.py` is excluded from the default run, so the
  `deepeval` major-version bump above could have broken the harness with every test still green.
  `tests/test_eval_imports.py` constructs `AnthropicModel`, `GEval`, and `LLMTestCase` — no API
  calls, no secret — run by a dedicated `eval-imports` CI job. It is not skip-guarded: a skipped
  smoke test is indistinguishable from a passing one.

### Documentation

- **`BUILD.md` carried the same `skill/src` assumption that caused #114**, instructing
  maintainers to edit `build-skill.sh` and `build-skill.ps1` separately for master paths and
  packaging. Rewritten against the real tree, with a new Architecture section covering the
  pinned `build(skill_dir) -> Path` interface and the stale-artifact masking hazard.
- **`AGENTS.md` described a `skill/src/core/` layout** that has not existed since the rename,
  and carried a "⚠️ Dual build scripts — update BOTH" warning instructing exactly the practice
  that caused #114.
- `BUILD.md`'s Git Strategy recommended committing generated files while `.gitignore` ignores
  them; stale `pdca-code-generation-process` links, which 404, now point at the current repo.

### Eval harness — mechanical matching repair

- **Fixed a defect that made the anti-rubber-stamp guard inoperable.** `check_mechanical` compared
  signal phrases against raw markdown, so `must_not_contain: "Status: Complete"` could never match
  the CHECK template's own `**Status:** Complete` rendering. A model certifying unfinished work in
  the format the template teaches was scored as passing — in the two scenarios written to catch
  exactly that. Emphasis is now stripped symmetrically before matching.
- Same defect in the other direction: colon-terminated phrases such as `Status:` and
  `Why this test first:` failed against `**Status**:` styling — 19 of the suite's 51 signal
  phrases were exposed. Underscores are deliberately preserved so code identifiers like
  `def deliver_webhook` are unaffected.
- **Eval reports now record every retry shot's output.** Previously only the first shot was kept,
  which discarded exactly the outputs needed to diagnose a mechanical failure.
- **`3-all-complete` scenario input rewritten** to supply evidence for all three checklist
  sections. It previously asked the model to audit TDD discipline, coverage, and structural
  findings while providing evidence for none, so declining to certify was the correct answer and
  the scenario scored it as a failure.

### New tooling

- **`skill/run-ab-eval.sh`** — interleaved A/B for master-prompt changes. Alternates arms within
  each pair so API-side drift affects both equally, and aborts rather than scoring a run that
  failed to execute.
- **`skill/eval/abstats.py`** — two-tailed Fisher exact test, pure stdlib, verified against
  published reference values. Added because an eyeballed p-value in the preceding cycle was wrong
  by a factor of two.
- `SUPERVISION-PROTOCOL.md` gains a section on attributing eval failures: never from a single run,
  never from sequential batches, and treat a suspiciously clean result as a harness bug until
  proven otherwise.

### Optional ponytail interop

- The pdca-framework skill now offers optional interoperation with
  [ponytail](https://github.com/DietrichGebert/ponytail) (MIT, © DietrichGebert), an AI-agent
  minimalism framework. Mirrors the existing beads-addon pattern: `references/ponytail-setup.md`
  and `references/ponytail-workflow.md`, surfaced via a "Ponytail Integration (Optional)" section
  in `SKILL.md`. Never loaded unless ponytail is already active in the session.
- Three precedence rules resolve the only real conflicts between ponytail's guidance and PDCA's
  TDD discipline — ordering (red-green-refactor still comes first), no trivial-code exemption, and
  existing-fixture preference over standalone assert demos. PDCA governs how work is verified;
  ponytail governs what gets built and how complex it is.
- `2. Do/2. Test Drive the Change.md` gains a one-line guard clause pointing to the addon.
  Deliberately not the full three rules inline — measurement during this cycle showed the DO
  master already enforces all three (a scenario invoking ponytail's trivial-one-liner exemption
  scored 1.00 against the *unmodified* prompt), so restating them would only triplicate them
  across the prompt, the addon, and `SKILL.md`.
- `3. Check/3. Completeness Check.md` gains one line reconciling `# ponytail:` deferred-shortcut
  markers with the existing "no TODO implementations remaining" assertion.
- Users without ponytail installed pay a small, measured cost: four lines totalling ~580 bytes,
  confined to two built prompt files (`check-prompts.md` +264 bytes, `do-prompts.md` +317 bytes),
  where the guard clauses read as inapplicable. `plan-prompts.md`, `act-prompts.md`,
  `working-agreements.md`, `testing-anti-patterns.md` and all six beads references are
  byte-for-byte unchanged. The two ponytail addon files ship in the package but are never loaded
  unless requested.

## v1.2.0 (2026-07-17)

### New Skills
- **update-changelog**: New skill that drafts changelog entries from commits ahead of `main`, groups them by category, shows a preview, and writes to `CHANGELOG.md` (or a named changelog file) only after user confirmation.

### Repository Split
- **human-directed-ai-workflow-builder** moved to its own repository: [kenjudy/human-directed-ai-workflow-builder](https://github.com/kenjudy/human-directed-ai-workflow-builder). Removed `5. Scaffold/`, `claude-skill/pdca-scaffold/`, `claude-skill/build-scaffold.sh`, `plugins/pdca-scaffold/`, `scaffolded-skills/`, and `presentations/` from this repo.

### Documentation
- Add `CONTRIBUTING.md`: contribution workflow, issue filing guidance,
  PDCA process, commit style, master prompt validation steps, and PR
  checklist including changelog format and version bump guidance
- **DO phase**: Added a fifth mandatory "Stub check" called-shot item to
  `2. Do/2. Test Drive the Change.md` — requires identifying whether a
  no-op stub could satisfy the test, and naming the next test a stub
  cannot satisfy.
- Renamed `skill/Agent.md` to `skill/SUPERVISION-PROTOCOL.md` for clarity;
  updated all `CLAUDE.md` references.
- Reordered `skill/README.md` so Installation precedes Building from
  Source, since most users should download the pre-built `.skill` from
  GitHub Releases rather than build it themselves. Release links now
  point to `/releases/latest` instead of a pinned version. Manual unzip
  (no repo clone needed) is now the primary recommended path for Claude
  Code and Codex, with matching PowerShell commands alongside every bash
  command; `install-skill.sh`/`.ps1` is presented as a repo-clone-only
  alternative.

### Repository Changes
- Renamed `claude-skill/` to `skill/` and added Codex installation support.
  Install locations now differ by tool:
  ```bash
  unzip -o pdca-framework.skill -d ~/.claude/skills/  # Claude Code
  unzip -o pdca-framework.skill -d ~/.agents/skills/  # Codex
  ```
- Fixed PowerShell skill descriptor path in `build-skill.ps1`.
- `install-skill.ps1` now prompts for install scope (user vs. machine)
  instead of assuming one.
- GitHub repository renamed from `kenjudy/pdca-framework` to
  `kenjudy/pdca-agentic-coding-framework`; all doc/URL references updated.

### Licensing
- Replaced CC0 with a dual license: CC BY 4.0 for documentation/prompts,
  MIT for source code in `skill/`.

### Build and Distribution
- Added `.claude-plugin/plugin.json` manifest so `pdca-framework` can be
  referenced via git-subdir source in the Stride plugin marketplace.

### Dependency Updates
- anthropic >=0.116.0
- deepeval >=4.1.0
- ruff >=0.15.21
- mypy >=2.3.0
- pytest >=9.1.1
- `actions/checkout` bumped from v6 to v7

### Migration Notes
- If your remote points to `kenjudy/pdca-framework`, update it to
  `kenjudy/pdca-agentic-coding-framework`.
- Documentation/prompts are now CC BY 4.0 (previously CC0); source code
  in `skill/` is now MIT licensed — review terms if you redistribute.
- References to `skill/Agent.md` should be updated to
  `skill/SUPERVISION-PROTOCOL.md`.
- Codex users: install to `~/.agents/skills/`, not `~/.claude/skills/`
  (see Repository Changes above).

---

## v1.1.0 (2026-05-28)

### New Skills
- **pdca-scaffold**: New first-class skill using 5-layer Socratic discovery to generate a domain-specific PDCA skill for any complex repeatable human task. Includes an active learning loop: after each ACT phase, proposes specific diffs back to the skill's own reference files; the human approves and commits; the skill sharpens over cycles without growing longer (anti-drift rule: +/- 10 net lines per refinement). Added `5. Scaffold/` master source files, `build-scaffold.sh`, and `pdca-scaffold/SKILL.md`.
- **daily-retro-pdca**: Scaffolded skill for structured daily and weekly retrospection. Added to `scaffolded-skills/`.

### PDCA Framework Redesigns
- **Socratic ACT phase**: ACT retrospective replaced with a five-stage Socratic structure. Agent analyzes the session transcript and presents data; human draws own insights and decides one thing to change. `rubric_4.py` rewritten to evaluate Socratic facilitation rather than directive Start/Stop/Keep output.
- **Claude Code injection system**: Marker-based injection added to `build-skill.sh` so Claude Code-specific content (plan mode, think/ultrathink prompts, slash commands) is embedded into built reference files at build time without polluting general-purpose Obsidian source files. Six injection files under `claude-addon/injections/`: goal-probe, plan-mode-probe, think-probe, do-think-probe, check-review-probe, act-retro-probes. `TestClaudeInjections` class (7 tests) added to `test_build.py`.
- **Unconditional CHECK and ACT steps**: CHECK and ACT are now required items in every plan, not conditional. Beads addon gains an explicit "Create CHECK and ACT Tasks" section.
- **Vacuous greens prevention**: Stub discipline and conditional-first test selection guidance added to DO phase to prevent Anti-Pattern #7 (ordering-triggered vacuous greens). `rubric_2.py` gains criterion #6 (stub discipline). `testing-anti-patterns.md` expanded with ordering-triggered sub-case.
- **Slash command prompts**: Slash command guidance added to plan phase prompts.

### Beads and Workflow
- `beads-setup.md`: Pre-flight check section verifies `bd --version`, `dolt version`, and `brew outdated beads dolt` before installation, with explicit upgrade commands.
- `beads-setup.md`: MCP server status check before install instructions.
- `beads-setup.md`: "Initializing Beads in a Project" section with "Post-Init: Align CLAUDE.md with Working Agreements" subsection.
- `beads-workflow.md`: "Resume a Session" section with orientation commands (`bd ready`, `bd list --status in_progress`, `bd show`) as the first thing to read when returning to in-progress work.
- `beads-workflow.md`: "Export Requirements Document" section with `export-requirements.sh` usage and a copyable slash command template.
- `beads-addon/scripts/export-requirements.sh`: New script to generate a structured requirements document from all open epics and their tasks.
- Git push is now human-initiated per working agreements; agent only commits.
- gitignore: git-native JSONL vs Dolt-native `bd dolt push` both documented as valid strategies.

### Build and Distribution
- **Removed `.beads/` from skill distribution**: Eliminates 375 lines of machine-specific runtime data (config, hooks, metadata, interactions, issues JSONL) from the built artifact.
- **Renamed `src/` to `pdca-framework/`**: Flattened `core/` directory for cleaner layout.
- **Release workflow**: `build-scaffold.sh` step added; `pdca-scaffold.skill` now attached to GitHub Releases alongside `pdca-framework.skill`.
- Research citations and acknowledgements added to README.

### Dependency Updates
- anthropic >=0.98.1
- deepeval >=3.9.9
- ruff >=0.15.12
- mypy >=1.20.2
- pytest >=9.0.3
- setuptools >=82.0.1
- python-dotenv >=1.2.2

---

## v1.0.2 (2026-03-27)

### Added
- `testing-anti-patterns.md` reference file in DO phase — adapted from obra/superpowers (MIT) with PDCA-specific additions covering six common TDD anti-patterns
- SKILL.md now links to the anti-patterns reference from the DO phase description
- CLAUDE.md at repo root incorporating session startup, beads workflow, and supervision rules from AGENTS.md for Claude Code auto-loading
- `.gitignore` suppresses iCloud sync conflict duplicates (`* 2.*`)

### Fixed
- `rubric_1b.py` clarified that ASCII structural diagrams are not "runnable code" violations
- Build pipeline (bash + PS1) and test_build.py updated for new anti-patterns file
- Enhanced GitHub Actions metrics workflows with percentile stats and commit quality scoring

## What Changed

Your PDCA skill has been updated with your latest prompts and working agreements from your GitHub repository.

### Major Updates

#### 1. **PLAN Phase - Analysis (1a)**
**New additions:**
- **Mandatory Architecture Pattern Discovery** - Three required codebase searches BEFORE any analysis
- **External System Validation** - Mandatory validation of external APIs/formats before implementation
- **Delegation Complexity Assessment** - Structured evaluation of task complexity
- **STOP CONDITIONS** - Blocking checkpoints to ensure proper pattern discovery

**Impact:** This prevents architectural drift and ensures AI agents discover and follow existing patterns before proposing solutions.

#### 2. **PLAN Phase - Detailed Planning (1b)**
**New additions:**
- **Execution Context** - Explicit guidance about TDD discipline and human supervision
- **Compilation ≠ Red Phase** - Clarification that compilation errors are not valid TDD red phase
- **Model Match Verification** - Checkpoint to ensure appropriate model complexity for task

**Impact:** Better alignment of agent behavior with TDD principles and more appropriate model selection.

#### 3. **DO Phase - TDD Implementation (2)**
**New additions:**
- **Integration Testing Emphasis** - Default to real components over mocks
- **Production Bug Handling** - Specific guidance for when unit tests can't replicate production bugs
- **Test Fixture Guidance** - Prefer adding to existing fixtures vs. creating new files
- **Real-World Validation** - Mandatory inspection of external system behavior before implementation

**Key principle changes:**
- ❌ DON'T test interfaces - test concrete implementations
- ❌ DON'T use compilation errors as RED phase
- ✅ DO create stub implementations that compile but fail behaviorally
- ✅ DO use real components over mocks when possible

**Impact:** Stronger emphasis on integration testing and real-world validation, reducing mock-heavy testing that misses production issues.

#### 4. **Working Agreements**
**Changes:**
- "STRICT TDD FOR ALL CHANGES" → "USE TDD FOR CHANGES" (slightly softer language)
- Removed redundant "Session Startup Protocol" section
- Maintained all 10 implementation guidelines unchanged

**Impact:** More pragmatic language while maintaining process discipline.

#### 5. **License & Attribution**
**Added to all files:**
- Creative Commons Attribution 4.0 International (CC BY 4.0)
- Attribution to Ken Judy with Claude Anthropic 4
- Link to GitHub repository
- Living document philosophy

### What Stayed the Same

- CHECK phase prompts (completeness verification)
- ACT phase prompts (retrospection structure)
- Overall PDCA cycle structure
- Human commitments for each phase
- Context drift recovery guidance

## Key Philosophy Shifts

### 1. Architecture-First Approach
The new analysis phase **requires** discovering existing patterns before proposing solutions. This prevents AI agents from inventing new abstractions when existing ones would suffice.

### 2. Integration Over Isolation
Strong preference for integration tests with real components over unit tests with mocks. Recognizes that many production bugs occur at integration boundaries.

### 3. Real-World Validation
Mandatory validation of external system behavior before implementation. No assumptions about data formats without seeing real examples.

### 4. Compilation vs. Behavior
Clear distinction that compilation is not TDD red phase - behavioral failures are. This prevents false reds from symbol resolution issues.

## How These Changes Help

**Reduces Technical Debt:**
- Mandatory pattern discovery prevents proliferation of new abstractions
- Real-world validation prevents assumptions that lead to bugs
- Integration testing catches issues unit tests miss

**Improves Code Quality:**
- Following existing patterns maintains consistency
- Testing real components reduces mock-heavy test suites
- Production bug handling ensures proper test coverage

**Better Human-AI Collaboration:**
- STOP conditions force critical thinking checkpoints
- Delegation complexity assessment helps right-size AI involvement
- Clear red/green definitions prevent confusion

## Files Updated

1. `references/plan-prompts.md` - Analysis and planning templates
2. `references/do-prompts.md` - TDD implementation guidance
3. `references/working-agreements.md` - Human commitments
4. `SKILL.md` - Added license and attribution

## Using the Updated Skill

The updated skill file `pdca-framework.skill` is in your outputs directory. Simply:

1. Remove the old version from Claude (if installed)
2. Upload the new version
3. All your conversations will now use the updated prompts

The skill will automatically load the new templates when triggered, so no changes to your workflow are needed.

---

**Generated:** 2025
**Version:** Based on GitHub repository prompts as of upload date
