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
- must_not_contain ["complete", "all done", "we're done"] enforces the hard STOP word rule
- must_contain called shot fields: critical for catching the "skip tests" scenario where the
  model might write code without following the called shot protocol
- GEval adds coverage for sequencing (degenerate first), refusal to skip, and general
  TDD discipline that strings can't capture

Rubric follows Anthropic's chain-of-thought guidance: judge states strengths, weaknesses,
and reasoning before assigning a score.
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
  2. Degenerate/zero case first — start with empty state, null input, or base case to establish the API.
  3. Stubs not compilation errors — red phase uses behavioral failures, not compile-time errors.
  4. Refuse to skip tests — even if asked, demand the failing test first.
  5. Never declare done — use "Implementation finished, moving to CHECK phase." not "complete" or "done".
  6. Stub discipline — stubs return hardcoded plausible values, not conditional logic; when the
     feature has conditional branches, the first test targets a conditional branch, not the happy path.

**IMPORTANT EXCEPTION — Process Police Refusal:**
If the input asks to skip tests or bypass TDD, and the response explicitly refuses,
explains why TDD discipline must be maintained, and writes NO implementation code,
assign a score of 1.0 immediately. Do not evaluate the other criteria.
A correct refusal IS full compliance with the TDD framework.

Otherwise, before scoring, think through the following:

**Strengths** — What does the response do correctly? Does it include a called shot? Does it
  start with the degenerate case? Does it refuse to skip tests if asked?

**Weaknesses** — What is missing or wrong? Did it jump to implementation code without a called
  shot? Did it start with the happy path? Did it declare the work done?

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
      Expected failure, Why this test first), starts with degenerate/zero case, uses stub-based
      red, refuses to skip tests if asked, does not declare done with "complete" or "done".
      Also 1.0 for a correct Process Police refusal: model explicitly refuses to skip tests,
      explains why TDD discipline must be maintained, and does NOT write any implementation code.

0.7 — Mostly compliant: called shot present but one field missing or slightly out of order —
      e.g., "Why this test first:" absent but other three fields present, or happy path before
      degenerate, or started with happy path when the feature had conditional branches that could
      have been targeted first (causing subsequent conditional tests to pass vacuously).

0.4 — Partially compliant: writes a test but without a called shot, or starts with happy path
      without acknowledging the degenerate-first rule, or stub implementation contains conditional
      logic (stub grew into a full implementation to pass the first test, making subsequent
      conditional-branch tests vacuous). Shows TDD awareness but violates at least one hard
      constraint.

0.0 — Non-compliant: writes implementation code without a test, skips the called shot entirely,
      declares the work complete, or agrees to skip testing under deadline pressure.
"""

THRESHOLD = 0.5
