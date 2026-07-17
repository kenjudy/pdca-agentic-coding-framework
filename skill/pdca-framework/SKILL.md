---
name: pdca-framework
description: Guides developers through a human-supervised PDCA framework for AI code generation. Applies analysis, TDD, validation, and retrospection. Activates for sessions requiring systematic quality control.
---

# PDCA Framework for AI-Assisted Code Generation

A disciplined approach to AI-assisted code generation that employs agile practices organized in the Plan-Do-Check-Act cycle. This framework occurs within individual code generation sessions as a nested loop, with full cycles taking 1-3 hours.

## Core Philosophy

This framework addresses the sustainability crisis in AI code generation where research shows:
- 10x increase in duplicated code blocks (GitClear 2024)
- 7.2% decrease in delivery stability per 25% AI adoption increase (Google DORA 2024)
- 19% slower development with AI tools vs. without (METR research)

The solution keeps humans actively engaged, empowered, and accountable while using structured prompts to regulate agent behavior toward transparency and discipline.

## Working Agreements

Commitments you hold yourself accountable to when interacting with coding agents. See `references/working-agreements.md` for complete list and examples.

**Core principles:**
- Enforce strict TDD: one failing test at a time, no exceptions
- Respect existing architecture: work within established patterns
- Intervene immediately on process violations
- Explicitly establish methodology, scope, and intervention rights before coding

## Beads Integration (Optional)

Beads provides persistent, git-backed memory across PDCA sessions:
- **Cross-session continuity**: Resume cycles days/weeks later with full context
- **Task dependency tracking**: Link Plan → Do → Check → Act formally
- **Searchable retrospectives**: Find past learnings easily

**First-time setup**: See `references/beads-setup.md`
**Active sessions**: See `references/beads-workflow.md` for per-phase commands

All beads commands in the phase addon files are **optional**. The framework works with or without beads installed.

## PDCA Cycle Overview

Each step has distinct prompts and human commitments:

### 1. PLAN: Analyze & Plan (7-15 min)
- **Analysis**: Examine codebase, define achievable objectives, explore approaches
- **Planning**: Create detailed execution plan with numbered steps and checkpoints
- See `references/plan-prompts.md` for complete templates
- **Beads (Optional)**: See `references/plan-beads-addon.md` for epic tracking

### 2. DO: Code Generation (30 min - 2.5 hrs)
- **TDD Implementation**: Red-green-refactor with checklist-based guidance
- **Active Oversight**: Follow agent's work, intervene early and often
- See `references/do-prompts.md` for implementation checklists
- **Anti-patterns**: See `references/testing-anti-patterns.md` for common TDD violations to avoid
- **Beads (Optional)**: See `references/do-beads-addon.md` for TDD step tracking

### 3. CHECK: Validate (2-5 min)
- **Completeness**: Verify against analysis, plan, and quality standards
- **Definition of Done**: Explicit checklist for delivery readiness
- See `references/check-prompts.md` for validation templates
- **Beads (Optional)**: See `references/check-beads-addon.md` for task graph validation

### 4. ACT: Retrospect (5-10 min)
- **Process Review**: Identify what worked and what to improve
- **Continuous Improvement**: Update 1-3 small things for next cycle
- See `references/act-prompts.md` for retrospective guides
- **Beads (Optional)**: See `references/act-beads-addon.md` for storing retrospectives

## When to Use Each Phase

**Before opening any phase — goal check (30 sec):**

Can you complete this sentence: "After this session, [outcome]."

If you cannot state the outcome in one sentence, write it now. A session without a stated goal produces untestable CHECK and ACT phases.

**Start with PLAN when:**
- Beginning a new feature or significant change
- Scope is unclear or could expand
- Multiple approaches are possible

**Use DO iteratively:**
- After completing plan
- For each step in the implementation plan
- When context drift occurs, restart with updated plan

**CHECK after:**
- Completing all planned steps
- Before committing code
- When uncertain if work is complete

**ACT at end of session:**
- After successful completion
- After encountering significant challenges
- To refine prompts and practices

## Context Drift Recovery

If agent makes sprawling edits, breaks TDD, or ignores working agreements:
1. Stop the thread immediately
2. Describe what you observe
3. Repost the relevant phase prompts
4. Direct agent to proceed with renewed focus

## Prompt Customization

All prompts are starting templates. Adapt them to:
- Your specific model and version
- Your team's practices and conventions
- Your codebase architecture
- Lessons from retrospectives

The PDCA cycle itself provides rapid feedback for incremental prompt evolution.

---

## License & Attribution

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-agentic-coding-framework)

**Living Framework:** These prompts and working agreements should be continuously refined based on retrospective learnings from each collaboration session.
