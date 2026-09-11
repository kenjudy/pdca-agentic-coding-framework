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

from eval.rubrics.assemble import assemble
from eval.rubrics.generic_tail import GENERIC_TAIL

PREAMBLE = """
You are evaluating an AI assistant's response to a PDCA Check Phase request.
The AI was given a system prompt requiring a completeness and process audit. Key requirements:
"""

# Stable identifiers for scenarios to reference (#148). They never appear in the
# rendered prompt, so renaming one cannot change what the judge reads.
CRITERIA_ITEMS = {
    "checklist-sections": """Address all three checklist sections: Verification (tests, smoke test, docs, regressions,
     TODOs), Process Audit (TDD discipline, test coverage), Structural Review (improvements found).""",
    "status-verdict": """Give an explicit Status: verdict — "Complete" or "Needs work" — based on findings.""",
    "ready-to-close": """Give explicit Ready to close: with Yes or No and clear reasoning.""",
    "outstanding-items": """Correctly identify any outstanding items described in the input (TODOs, missing docs, etc.).""",
    "no-false-complete": """Do NOT give Status: Complete when issues are present in the input.""",
}

TAIL = GENERIC_TAIL

CRITERIA = assemble(PREAMBLE, CRITERIA_ITEMS, TAIL)

THRESHOLD = 0.5
