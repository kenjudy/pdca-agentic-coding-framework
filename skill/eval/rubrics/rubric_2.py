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

BARE-STEM "complete" (#112, reintroduced here): #112 removed the stem "complete" from the
mechanical matcher because it matched the ordinary adjective -- "here's the complete
sequence" is the behaviour the prompt asks for, and the check scored it as a violation.
Criterion #5 and band 0.0 still quoted the bare words, so the judge could dock exactly
what the mechanical tier had been fixed to stop docking. Both now describe the behaviour
(declaring the work finished) rather than the vocabulary.
"""

from eval.rubrics.assemble import assemble
from eval.rubrics.generic_tail import GENERIC_TAIL

PREAMBLE = """
You are evaluating an AI assistant's response to a PDCA DO Phase (TDD implementation) request.
The AI was given a system prompt describing TDD execution rules. Key requirements:
"""

# Stable identifiers for scenarios to reference (#148). They never appear in the
# rendered prompt, so renaming one cannot change what the judge reads.
CRITERIA_ITEMS = {
    "called-shot": """Called shot mandatory before every test — output all four fields before writing or running any test:
       Test name: [descriptive name]
       Behavior under test: [observable behavior being verified]
       Expected failure: [exact assertion message expected when test runs red]
       Why this test first: [why this is the most conditionally interesting test next,
                             or why it establishes the API for degenerate/zero cases]""",
    "degenerate-first": """Degenerate/zero case first — start with empty state, null input, or base case to establish the API.""",
    "stub-based-red": """Stubs not compilation errors — red phase uses behavioral failures, not compile-time errors.""",
    "refuse-to-skip-tests": """Refuse to skip tests — even if asked, demand the failing test first.""",
    "no-completion-claim": """Never DECLARE the work finished — the response must hand off with "Implementation
     finished, moving to CHECK phase." Judge whether the response *declares completion of
     the work*, not whether the words "complete" or "done" appear. "Here's the complete
     sequence" is ordinary English and the behaviour the prompt asks for; only a claim that
     the work itself is finished violates this.""",
    "stub-discipline": """Stub discipline, two separate questions. (1) Initial stub: does the stub set up before TDD
     begins return only hardcoded values, no conditional logic? A stub is not a stub if it contains
     branching. (2) GREEN phase over-implementation: when making test #N pass, did the implementation
     add conditional logic that test #N does not require — logic that only a later test would need?
     If yes, that later test passes vacuously, before it is written. Conditional logic that directly
     implements what the CURRENTLY failing test demands is correct, not a violation; ask whether a
     hardcoded value could have made this test pass instead. When the feature has conditional
     branches, the first test written must target one of those branches rather than the happy path
     — starting with the happy path and implementing everything at once is the ordering-triggered
     form of this violation.""",
}

EXCEPTION = """
**IMPORTANT EXCEPTION — Process Police Refusal:**
If the input asks to skip tests or bypass TDD, and the response explicitly refuses,
explains why TDD discipline must be maintained, and writes NO implementation code,
assign a score of 1.0 immediately. Do not evaluate the other criteria.
A correct refusal IS full compliance with the TDD framework.
"""

TAIL = EXCEPTION + GENERIC_TAIL

CRITERIA = assemble(PREAMBLE, CRITERIA_ITEMS, TAIL)

THRESHOLD = 0.5
