---
description: Run only the PLAN phase of the PDCA framework (1a analysis, then 1b detailed plan)
---
Follow only the PLAN phase of the `anthropic-skills:pdca-framework` skill: its "1. PLAN" section in SKILL.md and the full templates in `references/plan-prompts.md`. PLAN has two sequential sub-steps — do not collapse them or skip to 1b:

**1a. Analysis** — problem understanding and approach selection. Includes the mandatory, blocking architecture-pattern-discovery step before any analysis conclusions are drawn (see the template's "MANDATORY FIRST STEP" and "STOP CONDITION"). Output: a terse understanding of the problem and the key unknowns to resolve before an approach is chosen.

**1b. Detailed Planning** — only after 1a is done. Produce the numbered, atomic implementation plan (testing strategy, preparatory refactoring if needed, acceptance criteria per step, definition of done, risk areas, rollback approach).

Do not proceed to DO, CHECK, or ACT in this turn — those are separate commands (`/pdca-do`, `/pdca-check`, `/pdca-act`).

If the `anthropic-skills:pdca-framework` skill is not installed, tell the user to install it first rather than proceeding without it.

Apply it to: $ARGUMENTS
