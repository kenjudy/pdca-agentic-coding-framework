---
description: Run only the DO phase of the PDCA framework (TDD implementation with active oversight)
---
Follow only the DO phase of the `anthropic-skills:pdca-framework` skill: its "2. DO" section in SKILL.md, the checklists in `references/do-prompts.md`, and the anti-patterns in `references/testing-anti-patterns.md`. Execute one plan step at a time under TDD discipline (one failing test at a time, no exceptions), with active oversight and early intervention. Do not proceed to PLAN, CHECK, or ACT in this turn — those are separate commands (`/pdca-plan`, `/pdca-check`, `/pdca-act`).

If the `anthropic-skills:pdca-framework` skill is not installed, tell the user to install it first rather than proceeding without it.

Apply it to: $ARGUMENTS
