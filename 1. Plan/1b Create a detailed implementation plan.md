# Planning Phase: Detailed Implementation Strategy

**Purpose:** Create trackable, atomic implementation steps optimized for AI execution
**When to use:** After completing analysis phase(s)
**Prerequisites:** Clear problem understanding and chosen approach from analysis
**Expected output:** Numbered implementation steps, testing strategy, process checkpoints
**Typical duration:** 2-5 minutes
**Next step:** Begin TDD implementation (2)
**Note:** Plan output is verbose and typically not added to ticket tracking

If available run this prompt in "Planning" mode.

<!-- CLAUDE_INJECT: plan-mode-probe -->

---
``` markdown

**Planning Phase** Based on our analysis, provide a coherent plan incorporating our refinements that is optimized for your use as context for the implementation:

**Execution Context:** This plan will be implemented in steps following TDD discipline with human supervision. Each step tagged for optimal model selection within the same thread context.

**Integration Strategy:**

- Map end-to-end data flow and all touch points
- Identify required changes to existing methods/interfaces
- Plan backward compatibility approach
- Consider file organization and naming consistency

**Testing Strategy:** Implementation follows TDD discipline — one failing test at a time. See DO phase for execution rules.

- Break the work into atomic, testable increments — one behavior per step
- For each step, identify the behavioral expectation to be verified (not implementation details)
- Build a test list: enumerate all behaviors to verify (golden path, degenerate cases, exceptions) as a planning artifact — execution is always one test at a time

**Preparatory Refactoring (if needed):**

Before behavioral steps begin, identify any structural cleanup required to make the feature change easy:
- [ ] Does any existing code need to be extracted, renamed, or reorganized to cleanly accommodate this change?
- [ ] If yes: list these as explicit first steps in the plan, tagged `refactor:` commits, before any `feat:` steps
- [ ] Preparatory refactoring steps must leave all existing tests passing — no behavioral change
- [ ] If none needed: explicitly confirm structure is ready as-is

**Multi-System Work:**

- [ ] Logical architecture identical across systems
- [ ] System-specific constraints checked (reserved keywords, etc.)

**Create actionable plan with:**

- Numbered implementation steps (small, testable increments) — each step is executed using the DO phase prompt
- ONE file/component per step when possible
- Acceptance criteria for each step
- Definition of done (tests pass + process followed)
- Risk areas to monitor
- Rollback approach if needed

**Process Checkpoints:**

- Complexity check: If a step feels too large to test atomically, split it
- Model match verification: Is the tagged model appropriate for actual complexity encountered?

**Full Cycle Scope:**

When the plan introduces a new skill, build script, command, or other artifact, the plan
must include explicit tasks — not implied — for each of the following:

- [ ] Build system: build script exists, is executable, produces correct output, command documented in CLAUDE.md
- [ ] Documentation: README updated, CLAUDE.md commands table updated
- [ ] CHECK: state what will be verified and against what criteria for this specific feature
- [ ] ACT: retrospective, working agreement updates proposed, issues closed

These are not cleanup items. Name them in the plan so CHECK can verify them like any other step.

At the end of your plan output, remind the human: "To execute each step, invoke PDCA Do. Do not begin any step without first opening that prompt."

```

_Plan is verbose and I don't add it to any tracking_

---

## License & Attribution

This template is part of the Human-AI PDCA Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Usage:** You are free to use, modify, and distribute this template with appropriate attribution. 

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-framework)

---
*2025*