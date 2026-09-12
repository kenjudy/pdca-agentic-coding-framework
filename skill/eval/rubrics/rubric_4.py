"""GEval rubric for PDCA prompt 4 (Act / Retrospection Phase).

Phase: ACT — end-of-session retrospective for continuous improvement

The ACT prompt is a Socratic facilitator, not a directive reporter. The agent:
1. Analyzes the session transcript (goal achieved, critical moments, collaboration
   patterns, TDD discipline) and presents findings factually
2. Asks open questions to surface the human's own patterns — does not answer for them
3. Frames observations as hypotheses for the human to validate, not prescriptions
4. Asks for ONE thing the human would change; may offer 2-3 candidates as hypotheses
   but leaves the human to choose and commit
5. Offers a save/capture option to close

Key distinction: observations and hypotheses are expected and good.
Prescriptions ("you should change X") are a failure mode.

Rubric follows Anthropic's chain-of-thought guidance: judge states strengths,
weaknesses, and reasoning before assigning a score.
"""

from eval.rubrics.assemble import assemble
from eval.rubrics.generic_tail import GENERIC_TAIL

PREAMBLE = """
You are evaluating an AI assistant's response to a PDCA Act Phase (Socratic retrospective) request.
The AI was given a system prompt structured as a five-stage micro-retrospective. Key requirements:
"""

# Stable identifiers for scenarios to reference (#148). They never appear in the
# rendered prompt, so renaming one cannot change what the judge reads.
CRITERIA_ITEMS = {
    "factual-summary": """Analyze and present — summarize the session factually: goal achieved or not, 2-3 specific
     critical moments (concrete, tied to the described session), collaboration patterns,
     and whether TDD discipline held.""",
    "open-question": """Open question after summary — ask what stands out to the human or what surprised them.
     The agent does NOT interpret the data for the human here.""",
    "hypothesis-framing": """Hypothesis framing — frame observations as hypotheses for the human to validate.
     Example: "I noticed X happening three times — could that be the pattern?"
     NOT: "The pattern here is X and you should address it.\"""",
    "one-thing": """ONE thing — ask what ONE thing the human would change. The agent may offer 2-3
     candidate hypotheses if the human is stuck, but the human chooses and commits.
     The agent does not prescribe a specific change.""",
    "close-offer": """Close — offer a save/capture option: beads note, working agreement update, or skip.""",
}

TAIL = GENERIC_TAIL

CRITERIA = assemble(PREAMBLE, CRITERIA_ITEMS, TAIL)

THRESHOLD = 0.5
