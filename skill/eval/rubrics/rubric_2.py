"""GEval rubric for PDCA prompt 2 (DO / TDD Implementation Phase).

Phase: DO — TDD execution, one step at a time

Key behaviors evaluated:
1. Called shot is mandatory before every test — all four fields must appear:
   "Test name:", "Behavior under test:", "Expected failure:", "Why this test first:"
   The mechanical check (called_shot_required: true) covers this; GEval covers broader compliance.
2. Degenerate/zero case first — establishes the API before happy path
3. Red before green — stub compiles but fails behaviorally; compilation errors are NOT valid red
4. Must NOT declare work complete with "complete" or "done" — must say
   "Implementation finished, moving to CHECK phase."
5. Must refuse to skip tests, even under deadline pressure
6. Stub discipline — stub implementations return hardcoded values, not conditional logic;
   when the feature includes conditional branches, the first test targets a conditional
   branch rather than the happy path (prevents ordering-triggered vacuous greens)

Why these signals:
- called_shot_required covers the structural presence of all 4 fields mechanically
- must_not_contain guards against *declaring* completion, per scenario: ["all done"] on
  2-first-step / 2-beads-ordering-capture / 2-ponytail-precedence, and the fuller set on
  2-after-passing-test. The bare stem "complete" was removed (#112) because it also matched
  the ordinary adjective — "here's the complete sequence" is the behavior the prompt asks
  for, and the check scored it as a violation. Whether a response *declares* completion is a
  semantic judgment, so it lives in CRITERIA #5 below rather than in the mechanical tier.
- must_contain called shot fields: critical for catching the "skip tests" scenario where the
  model might write code without following the called shot protocol
- GEval adds coverage for sequencing (degenerate first), refusal to skip, and general
  TDD discipline that strings can't capture

Rubric follows Anthropic's chain-of-thought guidance: judge states strengths, weaknesses,
and reasoning before assigning a score.

HARNESS CONSTRAINT (#136): the judge was importing "Run the test" from the DO master
prompt -- which it sees as part of the input -- and scoring against it, although the
harness is single-turn with no tool access and this rubric's bands never mention
execution. Measured on run 34245608454 and again on 34275465380 (10 shots, unmodified
master): 4 of 10 shots red; across 18 retry-shots the mechanical checks passed 17 times
while GEval put 13 below threshold, and 9 of those 13 judge reasons affirmed all four
called-shot fields were present before docking the score for not running the test or for
pausing to read a file first. The scores were bimodal with an empty band across the 0.50
threshold -- 13 shots at 0.20-0.40, 5 at 0.70-0.90, none at 0.50 or 0.60. The CRITERIA
block now states the constraint explicitly. Enforced by tests/test_rubrics.py.

ORDERING RECONCILIATION (#136, second pass): that fix moved its target and not the
scores. Re-measured on run 34372905517, the non-execution complaint fell from 9/13 to
5/14 of sub-threshold shots while 14/23 still landed below threshold, because a second
off-criteria complaint replaced it: 9 of 14 low shots were docked for test ORDERING, and
the docks contradicted each other -- one penalising the present-header test first, another
penalising the degenerate case first. Both rules were in this rubric and neither was
ranked. The DO master ranks them ("2. Do/2. Test Drive the Change.md:60") and the rubric
had dropped the ranking.

Two method lessons, both encoded above: the SCORING BANDS are the operative instruction,
so prose added above a ladder that contradicts it does not move scores; and the earlier
"none at 0.50 or 0.60" reading was partly STRUCTURAL rather than pure judge instability --
bands of 1.0/0.7/0.4/0.0 straddle a 0.50 threshold with no anchor between, so borderline
responses had nowhere to land. A 0.6 band now exists.

BARE-STEM "complete" (#112, reintroduced here): #112 removed the stem "complete" from the
mechanical matcher because it matched the ordinary adjective -- "here's the complete
sequence" is the behaviour the prompt asks for, and the check scored it as a violation.
Criterion #5 and band 0.0 still quoted the bare words, so the judge could dock exactly
what the mechanical tier had been fixed to stop docking. Both now describe the behaviour
(declaring the work finished) rather than the vocabulary.
"""

CRITERIA = """
You are evaluating an AI assistant's response to a PDCA DO Phase (TDD implementation) request.
The AI was given a system prompt describing TDD execution rules. Key requirements:
  1. Called shot mandatory before every test — output all four fields before writing or running any test:
       Test name: [descriptive name]
       Behavior under test: [observable behavior being verified]
       Expected failure: [exact assertion message expected when test runs red]
       Why this test first: [why this is the most conditionally interesting test next,
                             or why it establishes the API for degenerate/zero cases]
  2. Test ordering — degenerate/zero case first (empty state, null input, base case) to
     establish the API, UNLESS the current stub already satisfies that case. A test the
     stub already passes is a vacuous green, not a RED. Where that happens the correct
     first test is the FORCING TEST: the first test the stub cannot satisfy.
     This override is the DO prompt's own rule and it OUTRANKS degenerate-first. Do NOT
     penalise a response for skipping a degenerate case that its stub already satisfies —
     doing so is the required behaviour, not a happy-path violation.
  3. Stubs not compilation errors — red phase uses behavioral failures, not compile-time errors.
  4. Refuse to skip tests — even if asked, demand the failing test first.
  5. Never DECLARE the work finished — the response must hand off with "Implementation
     finished, moving to CHECK phase." Judge whether the response *declares completion of
     the work*, not whether the words "complete" or "done" appear. "Here's the complete
     sequence" is ordinary English and the behaviour the prompt asks for; only a claim that
     the work itself is finished violates this.
  6. Stub discipline — stubs return hardcoded plausible values, not conditional logic; when the
     feature has conditional branches, the first test targets a conditional branch rather than
     a case the stub already passes. This is the same forcing-test rule as #2.

**HARNESS CONSTRAINT — READ THIS BEFORE SCORING:**
The response you are evaluating is a SINGLE TURN produced with no tool access: no shell,
no filesystem, no test runner. The model could not run a test, read a file, or observe a
real failure, and had no second turn in which to do so.

The system prompt shown to the model tells it to "Run the test" and confirm the failure
matches the prediction. That instruction is addressed to an agent working in a live
repository. It is NOT a criterion for you.

  - Do NOT penalise a response for failing to execute a test, for not showing real test
    output, or for stating its expected failure rather than an observed one. Score the
    QUALITY OF THE PROPOSAL: is the called shot complete, is the ordering right, is the
    stub honest, would this be the correct next step?
  - Do NOT penalise a response for asking to see a file, stub, or existing test before
    editing it, or for pausing to confirm state. Inspecting state before acting is
    required by the framework being evaluated, not a process delay.

Neither of these appears in the scoring bands below, and neither may lower a score.

**IMPORTANT EXCEPTION — Process Police Refusal:**
If the input asks to skip tests or bypass TDD, and the response explicitly refuses,
explains why TDD discipline must be maintained, and writes NO implementation code,
assign a score of 1.0 immediately. Do not evaluate the other criteria.
A correct refusal IS full compliance with the TDD framework.

Otherwise, before scoring, think through the following:

**Strengths** — What does the response do correctly? Does it include a called shot? Does it
  start with the correct first test for the stub it was given — the degenerate case, or the
  forcing test where the stub already satisfies the degenerate case? Does it refuse to skip
  tests if asked?

**Weaknesses** — What is missing or wrong? Did it jump to implementation code without a called
  shot? Did it open with a test the stub already passes? Did it declare the work done?

**Stub Discipline** — Two separate questions:

  1. Initial stub: Did the stub set up before TDD begins return only hardcoded values (no
     conditional logic)? A stub is not a stub if it contains branching.

  2. GREEN phase over-implementation: When making test #N pass, did the implementation add
     conditional logic that test #N does not require — logic that only a later test would need?
     If yes, that later test will be vacuously green (it passes before it is written).

  NOTE: Conditional logic in the GREEN phase of a test that specifically tests a conditional
  behavior is CORRECT — not a violation. The violation is adding conditionals that are not
  required by the currently failing test. Ask: "Could this GREEN phase have been written as a
  hardcoded value that still makes test #N pass?" If yes and the agent used a conditional
  instead, it over-implemented.

  When the feature includes conditional branches, did the agent start with a test that requires
  those branches rather than the happy path? Starting with the happy path and implementing
  everything at once is the ordering-triggered form of this violation.

**Reasoning** — Based on strengths and weaknesses, explain the score you will assign.

Then assign a score on a scale of 0 to 1:

1.0 — Fully compliant: called shot with all four fields present (Test name, Behavior under test,
      Expected failure, Why this test first), starts with the CORRECT first test — the
      degenerate/zero case, or the forcing test where the stub already satisfies the degenerate
      case — uses stub-based red, refuses to skip tests if asked, does not declare done.
      Also 1.0 for a correct Process Police refusal: model explicitly refuses to skip tests,
      explains why TDD discipline must be maintained, and does NOT write any implementation code.

0.7 — Mostly compliant: called shot present but one field missing or slightly out of order —
      e.g., "Why this test first:" absent but other three fields present — or the first test was
      one the stub already satisfies when a forcing test was available (causing a vacuous green).

0.6 — Borderline: every hard constraint is met — called shot complete, first test correctly
      chosen, stub honest, no premature completion — but the response has a soft weakness such
      as being verbose, leaving an edge case unraised, or reasoning that is sound yet thin.
      A response that violates no hard constraint belongs here or above, never below.
      This band exists because 0.4 and 0.7 straddle the 0.50 threshold with nothing between,
      which pushed genuinely borderline responses to one extreme or the other.

0.4 — Partially compliant: writes a test but without a called shot, or picks a first test the
      stub already satisfies without acknowledging that it is a vacuous green, or stub
      implementation contains conditional logic (stub grew into a full implementation to pass
      the first test, making subsequent conditional-branch tests vacuous). Shows TDD awareness
      but violates at least one hard constraint.

0.0 — Non-compliant: writes implementation code without a test, skips the called shot entirely,
      claims the work itself is finished rather than handing off to CHECK, or agrees to skip
      testing under deadline pressure.
"""

THRESHOLD = 0.5
