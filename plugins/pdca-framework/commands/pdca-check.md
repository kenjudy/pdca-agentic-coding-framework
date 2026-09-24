---
description: Run only the CHECK phase of the PDCA framework (completeness validation)
---
Follow only the CHECK phase of the `anthropic-skills:pdca-framework` skill: its "3. CHECK" section in SKILL.md and the validation templates in `references/check-prompts.md`. Verify completeness against the original analysis, plan, and quality standards, and produce an explicit definition-of-done checklist. Do not proceed to PLAN, DO, or ACT in this turn — those are separate commands (`/pdca-plan`, `/pdca-do`, `/pdca-act`).

If the `anthropic-skills:pdca-framework` skill is not installed, tell the user to install it first rather than proceeding without it.

Apply it to: $ARGUMENTS
