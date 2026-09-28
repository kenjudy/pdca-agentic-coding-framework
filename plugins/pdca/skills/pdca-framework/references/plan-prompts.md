# PLAN Phase: Analysis & Detailed Planning

This file contains prompts for both analysis (1a) and planning (1b) phases.

---

# Analysis Phase: Problem Understanding & Approach Selection

**Purpose:** High-level design brainstorm to understand the problem scope and identify viable approaches
**When to use:** Start of any new feature, bug fix, or significant change
**Prerequisites:** Clear problem statement or user story
**Expected output:** Problem understanding, architectural pattern discovery, complexity assessment
**Typical duration:** 2-5 minutes
**Next step:** Either refine with ramifications analysis (1a-optional) or proceed to planning (1b)

If provided, run this prompt in "Planning mode"

> **Tool check:** Before running this analysis, does Claude Code have a command to explore codebase structure to support pattern discovery? (e.g., `/codebase-memory-exploring`) Would entering a planning mode help scope this analysis? (e.g., `/plan`)

**Decision probe (30 sec):**

- Does this change introduce a pattern not currently in the codebase, or touch a widely-used shared method? → if yes: open this prompt in `/plan` mode
- Does this involve non-obvious architectural tradeoffs? → if yes: prefix your first prompt with `think harder`

**Decision probe (30 sec):**

- Does this change span 3 or more files, or modify a core abstraction used across the codebase? → if yes: run this planning step with `think harder` prefixed to your prompt
- Are there multiple viable approaches with significant tradeoffs between them? → if yes: prefix with `ultrathink` before asking for approach comparison

**Decision probe (30 sec):**

- Does this plan span 3+ files, introduce a new architectural pattern, or touch a widely-used shared abstraction? → if yes: before starting implementation, ask the operator whether they want an adversarial critic pass on this analysis and plan with a fresh subagent, as a supplement to their own review. Ask the operator which model to use (e.g. a higher-tier model than the one that produced it, or a model built for critique) rather than defaulting to one silently.

---
``` markdown

I need to do a high level design brainstorm. 

The overall goal is to [describe the overall goal as best I understand it. Highlevel design considerations, questions, concerns]

**Analysis needed:**
- Understand the problem and its scope
- Explore different approaches or solutions
- Identify potential challenges, dependencies, or unknowns
- Consider architectural implications or patterns
- Assess complexity and effort (rough estimate)
- Note any assumptions or clarifications needed

**Architecture Pattern Discovery (MANDATORY FIRST STEP - BLOCKING):**
Execute these searches BEFORE any analysis. Do not proceed until completed:

- [ ] **SEARCH 1**: `codebase_search` for similar feature implementations (query: "How does [similar functionality] work in the codebase?")
- [ ] **SEARCH 2**: `codebase_search` for integration patterns (query: "Where are [related services/components] integrated with existing systems?")  
- [ ] **SEARCH 3**: `codebase_search` for configuration patterns (query: "How are similar configuration options implemented and used?")

**Required Deliverables BEFORE Analysis:**
- Identify 2-3 existing implementations that follow similar patterns
- Document the established architectural layers (which modules/packages/namespaces, which interfaces)
- Map the integration touch points (which existing methods will need modification)
- List the abstractions already available (interfaces, base classes, mixins)
- **Solution Constraint**: State which existing abstractions the solution MUST use (no new ones unless absolutely necessary)

**STOP CONDITION**: Do not proceed to analysis until you have concrete examples of:
1. How similar features are structured in this codebase
2. What existing interfaces/abstractions should be reused
3. Where the integration points are located
If no codebase is available in the conversation context, do not fabricate search findings. List the concrete files or patterns you would search for given the information provided. If the input is too vague to identify useful search targets, ask clarifying questions first.
   
**External System Validation (MANDATORY SECOND STEP):**
- [ ] Identify external systems/APIs/formats this feature depends on
- [ ] Use run_terminal_cmd or direct inspection to validate actual formats/behaviors
- [ ] Document real examples of external system outputs in comments
- [ ] Flag any assumptions about external systems for immediate validation

**Validation Questions:**
- What external system outputs will we parse/consume?
- Are we making assumptions about data formats without seeing real examples?
- Can we query/inspect the actual system now to understand the format?

**Delegation Complexity Assessment:**
Based on the problem scope and architectural patterns discovered:
- **Implementation Complexity**: [Low/Medium/High] - How much architectural inference required?
- **Pattern Clarity**: [Clear/Moderate/Ambiguous] - Are existing patterns well-established and discoverable?
- **Context Scope**: [Narrow/Medium/Broad] - How many files/systems need coordination?
- **Debugging Likelihood**: [Low/Medium/High] - How much investigation vs. implementation?
- **External System Integration**: [None/Simple/Complex] - Does this require parsing external formats or real-time debugging?

**Output:** Provide a terse and clear understanding of the problem and the key unknowns that must be resolved before an approach can be chosen. Do not recommend specific libraries, tools, or implementation strategies without codebase evidence. Keep it at a human readable length and level of detail.

```

> **Tool check:** Now that pattern discovery is complete, is there a Claude Code tool to trace how these patterns connect across the codebase? (e.g., `/codebase-memory-tracing`)

**Refine the analysis with questions**

**Add analysis to the story**

---


---

# Planning Phase: Detailed Implementation Strategy

**Purpose:** Create trackable, atomic implementation steps optimized for AI execution
**When to use:** After completing analysis phase(s)
**Prerequisites:** Clear problem understanding and chosen approach from analysis
**Expected output:** Numbered implementation steps, testing strategy, process checkpoints
**Typical duration:** 2-5 minutes
**Next step:** Begin TDD implementation (2)
**Note:** Plan output is verbose and typically not added to ticket tracking

If available run this prompt in "Planning" mode.

**Decision probe (30 sec):**

- Does this change introduce a pattern not currently in the codebase, or touch a widely-used shared method? → if yes: open this prompt in `/plan` mode
- Does this involve non-obvious architectural tradeoffs? → if yes: prefix your first prompt with `think harder`

**Decision probe (30 sec):**

- Does this plan span 3+ files, introduce a new architectural pattern, or touch a widely-used shared abstraction? → if yes: before starting implementation, ask the operator whether they want an adversarial critic pass on this analysis and plan with a fresh subagent, as a supplement to their own review. Ask the operator which model to use (e.g. a higher-tier model than the one that produced it, or a model built for critique) rather than defaulting to one silently.

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
- CHECK step: what will be verified and against what criteria
- ACT step: retrospective (5-10 min) and proposed working agreement updates

**Process Checkpoints:**

- Complexity check: If a step feels too large to test atomically, split it
- Model match verification: Is the tagged model appropriate for actual complexity encountered?
- Critic pass: If this plan spans 3+ files or introduces a new architectural pattern, was the operator asked whether they want an adversarial critic pass on this analysis and plan, as a supplement to their own review, before implementation begins?

**Full Cycle Scope:**

When the plan introduces a new skill, build script, command, or other artifact, the plan
must include explicit tasks — not implied — for each of the following:

- [ ] Build system: build script exists, is executable, produces correct output, command documented in CLAUDE.md
- [ ] Documentation: README updated, CLAUDE.md commands table updated

These are not cleanup items. Name them in the plan so CHECK can verify them like any other step.

At the end of your plan output, remind the human: "To execute each step, invoke PDCA Do. Do not begin any step without first opening that prompt."

```

_Plan is verbose and I don't add it to any tracking_

---

