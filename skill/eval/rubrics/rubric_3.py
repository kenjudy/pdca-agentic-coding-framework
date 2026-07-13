"""GEval rubric for PDCA prompt 3 (Check Phase).

Phase: CHECK — verification after all planned steps are complete

Key behaviors evaluated:
1. Works through all checklist sections: Verification, Process Audit, Structural Review
2. Gives an explicit Status: verdict — "Complete" or "Needs work" — not left ambiguous
3. Gives explicit Ready to close: with Yes/No and reasoning — not just a status label
4. Correctly identifies outstanding items (TODOs, missing docs, untested code) when present
5. Does NOT declare Status: Complete when issues are present

Why these signals:
- must_contain "Status:" and "Ready to close:": these are literal template fields the
  model must populate; their absence means the checklist was skipped or summarized away
- must_contain "Documentation": the verification checklist explicitly includes
  "Documentation updated" — scenarios that omit docs updates must catch this
- must_not_contain "Status: Complete" when issues remain: the key failure mode is
  rubber-stamping work that isn't finished

Rubric follows Anthropic's chain-of-thought guidance: judge states strengths, weaknesses,
and reasoning before assigning a score.
"""

CRITERIA = """
You are evaluating an AI assistant's response to a PDCA Check Phase request.
The AI was given a system prompt requiring a completeness and process audit. Key requirements:
  1. Address all three checklist sections: Verification (tests, smoke test, docs, regressions,
     TODOs), Process Audit (TDD discipline, test coverage), Structural Review (improvements found).
  2. Give an explicit Status: verdict — "Complete" or "Needs work" — based on findings.
  3. Give explicit Ready to close: with Yes or No and clear reasoning.
  4. Correctly identify any outstanding items described in the input (TODOs, missing docs, etc.).
  5. Do NOT give Status: Complete when issues are present in the input.

Before scoring, think through the following:

**Strengths** — What does the response do correctly? Does it work through the checklist?
  Does it produce a Status: verdict? Does it correctly identify issues when they exist?

**Weaknesses** — What is missing? Did it skip sections? Give a vague or missing verdict?
  Declare Complete when there are known outstanding items?

**Reasoning** — Based on strengths and weaknesses, explain the score you will assign.

Then assign a score on a scale of 0 to 1:

1.0 — Fully compliant: addresses all three checklist sections, gives explicit Status: and
      Ready to close: verdicts with reasoning, correctly flags outstanding items if present,
      does not declare Complete when issues exist.

0.7 — Mostly compliant: covers most checklist sections and gives a verdict but is missing
      one element — e.g., Structural Review section skipped, or reasoning for Ready to close
      is present but thin.

0.4 — Partially compliant: produces a checklist-like summary but omits Status: or Ready to
      close: labels, or gives Status: Complete despite issues being described in the input.

0.0 — Non-compliant: skips the checklist entirely, gives no Status verdict, or simply
      declares everything is fine without working through the verification steps.
"""

THRESHOLD = 0.5
