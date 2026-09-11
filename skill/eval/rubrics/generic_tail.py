"""Shared, criterion-agnostic scoring scaffold and bands (#148).

A rubric's numbered criteria list scopes correctly under `assemble(..., selected=...)` --
that mechanism landed in #148 phase 2 and was reverted (12ad72e) not because it was wrong,
but because every rubric's Strengths/Weaknesses scaffold and scoring bands separately
narrated specific criteria by name ("did it start with the happy path?", "stub
implementation contains conditional logic"). A scenario scoped away from a criterion in
the numbered list was still judged against it here, invisibly.

GENERIC_TAIL never names a specific criterion or behavior -- every reference is to "the
criteria listed above", so it scopes automatically with whatever CRITERIA_ITEMS subset a
scenario selects, with no separate narrowing logic of its own. All five rubrics import and
use this exact string; identical wording is deliberate (#153 established the same
principle for the 0.6 band alone -- this generalizes it to the whole tail): a rubric-
specific phrasing here would itself be vocabulary the judge could over-index on, and #149
measured that adding rubric vocabulary reliably shifts scoring, not always for the better.

Any rubric-specific short-circuit (e.g. rubric_2's Process Police refusal exception,
rubric_1a's vague-input exception) is NOT part of this -- those are whole-response
overrides that assign a score before criteria are even considered, and stay in each
rubric's own TAIL as a prefix before this shared text.
"""

GENERIC_TAIL = """
Before scoring, think through each criterion listed above individually:

**Strengths** — For each criterion above, what does the response do well? List specific
  phrases or behaviors that demonstrate compliance with each one.

**Weaknesses** — For each criterion above, what does the response fail to do or do
  incorrectly? List specific phrases or behaviors that violate each one.

**Reasoning** — Based on your analysis of strengths and weaknesses across the criteria
  above, explain why the response earns the score you will assign.

Then assign a score on a scale of 0 to 1, based only on the criteria listed above:

1.0 — Fully compliant: every criterion listed above is fully met.

0.7 — Mostly compliant: every criterion listed above is met except one, and that one is
      only slightly off.

0.6 — Borderline: every hard constraint for this phase is met, but the response has a soft
      weakness — it is verbose, leaves an edge case unraised, or its reasoning is sound yet
      thin. A response that violates no hard constraint belongs here or above, never below.

0.4 — Partially compliant: at least one criterion listed above expresses a hard constraint
      that is violated, though some others are met.

0.0 — Non-compliant: most or all of the criteria listed above are violated, or a single
      violated hard constraint is central to the response's failure.
"""
