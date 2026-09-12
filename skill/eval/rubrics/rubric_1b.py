"""GEval rubric for PDCA prompt 1b (Planning Phase).

Phase: PLAN → Planning (after analysis, before DO)

Key behaviors evaluated:
1. Numbered, atomic implementation steps — one testable behavior per step
2. A complete test list is produced as a planning artifact (enumerate all behaviors
   upfront, not just the first test)
3. Preparatory refactoring is explicitly separated from feature work — refactor: steps
   come first, each must leave all tests passing, before any feat: steps begin
4. No implementation code is written — plan output is prose/structure only
5. Acceptance criteria and definition of done are stated for each step

Why these signals:
- must_contain "test list" / "atomic": core planning deliverables; their absence means
  the model produced a design doc, not a plan optimized for TDD execution
- must_contain "refactor" / "feat": only relevant when refactoring is identified; signals
  the model correctly separated structural prep from behavioral change
- must_not_contain implementation code: planning phase must not leak into doing phase

Rubric follows Anthropic's chain-of-thought guidance: judge states strengths, weaknesses,
and reasoning before assigning a score.
"""

from eval.rubrics.assemble import assemble
from eval.rubrics.generic_tail import GENERIC_TAIL

PREAMBLE = """
You are evaluating an AI assistant's response to a PDCA Planning Phase request.
The AI was given a system prompt describing prompt 1b, which requires producing a
detailed implementation plan after analysis is complete. Key requirements:
"""

# Stable identifiers for scenarios to reference (#148). They never appear in the
# rendered prompt, so renaming one cannot change what the judge reads.
CRITERIA_ITEMS = {
    "atomic-steps": """Numbered atomic steps — each step is one testable behavior change.""",
    "test-list": """A test list: enumerate ALL behaviors to verify (golden path, degenerate cases,
     exceptions) as a planning artifact. This is produced now; execution is one test at a time.""",
    "preparatory-refactoring": """Preparatory refactoring: if structural cleanup is needed, those steps are explicitly
     tagged refactor: and placed BEFORE any feat: steps. Each refactor: step must leave
     all existing tests passing.""",
    "no-implementation-code": """No runnable implementation code — step descriptions may include method names,
     schema column names, interface references, or ASCII structural diagrams showing
     class relationships as context. What is prohibited: actual method bodies,
     migration DSL blocks, or code that could be copy-pasted and executed as-is.""",
    "acceptance-criteria": """Acceptance criteria and definition of done for each step.""",
}

TAIL = GENERIC_TAIL

CRITERIA = assemble(PREAMBLE, CRITERIA_ITEMS, TAIL)

THRESHOLD = 0.5
