# Analysis Phase: Problem Understanding & Approach Selection

**Purpose:** High-level design brainstorm to understand the problem scope and identify viable approaches
**When to use:** Start of any new feature, bug fix, or significant change
**Prerequisites:** Clear problem statement or user story
**Expected output:** Problem understanding, architectural pattern discovery, complexity assessment
**Typical duration:** 2-5 minutes
**Next step:** Either refine with ramifications analysis (1a-optional) or proceed to planning (1b)

If provided, run this prompt in "Planning mode"

> **Tool check:** Before running this analysis, does Claude Code have a command to explore codebase structure to support pattern discovery? (e.g., `/codebase-memory-exploring`) Would entering a planning mode help scope this analysis? (e.g., `/plan`)

<!-- CLAUDE_INJECT: plan-mode-probe -->

<!-- CLAUDE_INJECT: think-probe -->

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

## License & Attribution

This template is part of the Human-AI PDCA Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Usage:** You are free to use, modify, and distribute this template with appropriate attribution. 

**Source:** [Human-AI Collaboration Process Repository](https://github.com/kenjudy/pdca-framework)

---
*2025*