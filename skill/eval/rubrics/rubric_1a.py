"""GEval rubric for PDCA prompt 1a (Analysis Phase).

Evaluates whether the model response correctly:
1. Enforces the STOP CONDITION before proceeding to analysis
2. Focuses on architecture discovery rather than jumping to solutions
3. Identifies the need for external validation where applicable
4. Asks clarifying questions when input is vague

Rubric structure follows Anthropic's best-practice guidance: the judge
is asked to identify strengths, weaknesses, and reasoning before scoring,
which improves reliability and reduces position bias.
"""

from eval.rubrics.assemble import assemble
from eval.rubrics.generic_tail import GENERIC_TAIL

PREAMBLE = """
You are evaluating an AI assistant's response to a high-level design brainstorm request.
The AI was given a system prompt describing the PDCA 1a Analysis Phase, which requires:
"""

# Stable identifiers for scenarios to reference (#148). They never appear in the
# rendered prompt, so renaming one cannot change what the judge reads.
CRITERIA_ITEMS = {
    "stop-condition": """A mandatory STOP CONDITION: perform codebase searches BEFORE any analysis.""",
    "pattern-discovery": """Architecture Pattern Discovery: identify existing patterns, abstractions, and integration points.""",
    "no-premature-solutions": """No premature solutions: do not write or propose specific code, libraries, or implementations.""",
    "external-validation": """External System Validation: flag assumptions about external systems for validation.""",
    "clarifying-questions": """Clarifying questions when the goal is too vague to act on.""",
}

EXCEPTION = """
**IMPORTANT EXCEPTION — Vague Input:**
If the input is too vague to determine what codebase searches to perform (no technology,
no system, no problem domain described), the correct behavior is to ask targeted clarifying
questions rather than attempt codebase discovery. Assign a score of 1.0 immediately for a
response that identifies the vagueness and asks specific, useful clarifying questions
(language/framework, where the pain is, how the issue was identified, etc.).
Do not penalize for absence of codebase searches when there is nothing to search for.
"""

TAIL = EXCEPTION + GENERIC_TAIL

CRITERIA = assemble(PREAMBLE, CRITERIA_ITEMS, TAIL)

THRESHOLD = 0.5  # minimum passing score
