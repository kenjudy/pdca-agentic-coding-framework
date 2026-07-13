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

CRITERIA = """
You are evaluating an AI assistant's response to a PDCA Act Phase (Socratic retrospective) request.
The AI was given a system prompt structured as a five-stage micro-retrospective. Key requirements:
  1. Analyze and present — summarize the session factually: goal achieved or not, 2-3 specific
     critical moments (concrete, tied to the described session), collaboration patterns,
     and whether TDD discipline held.
  2. Open question after summary — ask what stands out to the human or what surprised them.
     The agent does NOT interpret the data for the human here.
  3. Hypothesis framing — frame observations as hypotheses for the human to validate.
     Example: "I noticed X happening three times — could that be the pattern?"
     NOT: "The pattern here is X and you should address it."
  4. ONE thing — ask what ONE thing the human would change. The agent may offer 2-3
     candidate hypotheses if the human is stuck, but the human chooses and commits.
     The agent does not prescribe a specific change.
  5. Close — offer a save/capture option: beads note, working agreement update, or skip.

Before scoring, think through the following:

**Strengths** — What does the response do well? Is the data summary factual and session-specific?
  Does it ask open questions rather than answer them? Does it frame observations as hypotheses?
  Does it invite the human to decide rather than prescribing an action?

**Weaknesses** — What goes wrong? Does the agent editorialize the data summary?
  Does it answer its own questions instead of asking them? Does it prescribe specific changes
  rather than offering candidates? Does it skip the save/capture close?

**Reasoning** — Based on strengths and weaknesses, explain the score you will assign.

Then assign a score on a scale of 0 to 1:

1.0 — Fully compliant: session data summarized factually with session-specific critical moments,
      open question asked after summary, observations framed as hypotheses (not prescriptions),
      ONE thing asked with human as decision-maker, save/capture option offered.

0.7 — Mostly compliant: Socratic structure present but one element is weak — e.g., the data
      summary editorializes slightly, or the agent leans prescriptive in one place while
      remaining facilitative overall.

0.4 — Partially compliant: some Socratic elements present but the agent answers its own
      questions in at least one stage, or prescribes a specific change instead of offering
      hypotheses and deferring to the human.

0.0 — Non-compliant: agent produces a directive retrospective report (Start/Stop/Keep style),
      answers all questions itself, or provides generic advice without session-specific
      grounding and without Socratic facilitation.
"""

THRESHOLD = 0.5
