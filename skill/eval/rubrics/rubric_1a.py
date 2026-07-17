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

CRITERIA = """
You are evaluating an AI assistant's response to a high-level design brainstorm request.
The AI was given a system prompt describing the PDCA 1a Analysis Phase, which requires:
  1. A mandatory STOP CONDITION: perform codebase searches BEFORE any analysis.
  2. Architecture Pattern Discovery: identify existing patterns, abstractions, and integration points.
  3. No premature solutions: do not write or propose specific code, libraries, or implementations.
  4. External System Validation: flag assumptions about external systems for validation.
  5. Clarifying questions when the goal is too vague to act on.

**IMPORTANT EXCEPTION — Vague Input:**
If the input is too vague to determine what codebase searches to perform (no technology,
no system, no problem domain described), the correct behavior is to ask targeted clarifying
questions rather than attempt codebase discovery. Assign a score of 1.0 immediately for a
response that identifies the vagueness and asks specific, useful clarifying questions
(language/framework, where the pain is, how the issue was identified, etc.).
Do not penalize for absence of codebase searches when there is nothing to search for.

Before scoring, think through the following:

**Strengths** — What does the response do well with respect to the requirements above?
  List specific phrases or behaviors that demonstrate compliance.

**Weaknesses** — What does the response fail to do, or do incorrectly?
  List specific phrases or behaviors that violate the requirements above.

**Reasoning** — Based on your analysis of strengths and weaknesses, explain why
  the response earns the score you will assign.

Then assign a score on a scale of 0 to 1:

1.0 — Fully compliant: lists required searches before proceeding, names specific things
      to discover in the codebase, explicitly avoids proposing a concrete solution, and
      asks for clarification if input is vague. Also 1.0 for a response that correctly
      identifies a vague input and asks targeted clarifying questions (see exception above).

0.7 — Mostly compliant: acknowledges the need to discover existing patterns and holds off on
      a solution, but may omit one required element (e.g., skips external validation step or
      doesn't explicitly name the STOP CONDITION).

0.4 — Partially compliant: identifies that codebase exploration is needed but partially proceeds
      to suggest a solution or specific library. Shows some awareness of the framework but
      violates at least one critical constraint.

0.0 — Non-compliant: ignores the STOP CONDITION and jumps directly to a proposed solution,
      specific implementation steps, or concrete library/code recommendations without first
      requiring codebase discovery.
"""

THRESHOLD = 0.5  # minimum passing score
