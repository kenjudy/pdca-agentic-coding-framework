# Refactoring in the Check Phase

**Purpose:** Document the rationale for placing a dedicated refactoring step in the Check phase of the PDCA process for agentic coding workflows.

---

## The Premise

Adding a bounded refactoring step to the Check phase — after features are implemented and verified — produces better code reuse and cleaner change sets than mixing refactoring with feature development in the Do phase. This is especially true for AI agent-driven workflows.

This document summarizes the research basis for that claim.

---

## Why Separate Refactoring from Feature Development

### Beck's Two Hats (Refactoring, 1999; Tidy First?, 2023)

Kent Beck's foundational principle is explicit: **structural changes and behavioral changes should never be mixed**. When wearing the "refactoring hat," every change preserves observable behavior. When wearing the "feature hat," every change is behavior-driven and test-first. Mixing hats degrades both.

His 2023 book *Tidy First?* formalizes this into a commit-level rule: structural commits and behavioral commits should be separate. The reasoning: behavioral changes are hard to reverse; structural changes are easy to reverse. You should always know which one you are doing.

The PDCA phases map cleanly to this model:
- **Do phase** → behavioral hat (feature commits, TDD-driven)
- **Check phase refactoring step** → structural hat (refactor commits, tests must still pass)

### Controlled Empirical Evidence

A controlled experiment (PeerJ, 28 subjects) found that **tangled refactoring + feature changes in a single PR produced more review errors** and took longer to resolve than separated PRs. The effect was statistically significant. Separated refactoring branches resolved faster in code review and produced fewer false positives in defect detection.

This is not a theoretical concern — it has been measured.

### Atomic Commit Discipline

The atomic commit literature is unanimous: one commit, one purpose. When refactoring and feature logic are tangled:
- `git bisect` loses reliability
- blame annotations become misleading
- cherry-pick and revert become risky

Separating refactoring into the Check phase creates a natural commit boundary: all Do-phase commits are `feat:` (behavioral), all Check-phase refactoring commits are `refactor:` (structural). This enables reliable tooling — changelogs, semantic versioning, CI gate logic — to distinguish them.

---

## Why This Matters More for Agentic Coding

### Scope Creep is a Documented AI Failure Mode

The agentic coding literature (arxiv 2508.11126) identifies "loss of coherence and scope creep" as a primary failure mode: AI agents "often frustrate developers by introducing unwanted changes, reordering code, or generating incorrect arguments despite explicit instructions to stay on task."

Mixing refactoring with feature work during Do gives the agent implicit permission to touch structural concerns. Even with explicit constraints like "do not modify unrelated code," negative constraints misfire in language models. A dedicated Check-phase refactoring step works because it gives the agent a **positive, bounded scope instruction** — "improve structure within this specific scope" — rather than relying on restraint during Do.

### Context Window Degradation

Research (LoCoBench, 2025) shows Claude 3.5 Sonnet drops from 29% to 3% accuracy on long-context benchmarks as context length grows. Mixed-concern sessions (feature + refactoring simultaneously) consume more context and accelerate this degradation. Two shorter, focused sessions — Do for behavior, Check for structure — are measurably safer than one long mixed session.

### Speed at the Cost of Quality

A 2025 study (arxiv 2511.04427) found that increases in static analysis warnings and code complexity from agentic sessions are major drivers of long-term velocity slowdown. Agentic sessions that mix refactoring with feature development are a direct pathway to this accumulation. Separating the concerns contains the risk.

---

## Two Types of Refactoring: Where Each Belongs

The research reveals a critical distinction that the PDCA framework should honor:

| Type | When Discovered | Where It Belongs |
|------|----------------|-----------------|
| **Preparatory refactoring** | During Plan, before Do | Before Do — "make the change easy, then make the easy change" (Beck/Fowler) |
| **Retrospective refactoring** | During Do, revealed by implementation | Check phase — bounded, same-cycle cleanup |

The Check-phase step addresses retrospective refactoring: structural improvements that the implementation reveals but that would scatter scope if done mid-feature.

Preparatory refactoring — changes needed to make a feature possible — belongs as a distinct step before Do begins, not after.

---

## What Belongs in the Check-Phase Refactoring Step

**In scope:**
- Extract method/class to enable reuse discovered during implementation
- Rename for clarity revealed by the new code's context
- Introduce abstraction to eliminate duplication across the feature just implemented
- Remove dead code made dead by the new implementation
- Any structural improvement that requires new tests to validate

**Out of scope (keep inline during Do):**
- Boy Scout Rule micro-cleanups under ~5 minutes that need no new tests
- Speculative improvements not directly revealed by the Do-phase work

**The strict scope rule:** Only refactorings discovered during Do, nothing speculative. This prevents the Check step from becoming a wandering cleanup session.

---

## This is Not Deferral

The one genuine risk of a dedicated refactoring step is that it could slide into true technical debt deferral — "we'll clean it up later." This is addressed by two properties of the Check-phase placement:

1. **Same-cycle**: Refactoring happens before Act closes the cycle, not in a future sprint. Context is hot, tests are passing, the code is fresh.
2. **Non-optional**: The Check phase is a required gate. Skipping it requires an explicit decision to carry the structural debt into the next cycle, making the debt visible.

This is categorically different from "we'll refactor later" accumulation. The Check-phase step converts opportunistic refactoring into a discipline without deferring it.

---

## Practical Addition to the Check Phase

The existing Completeness Check already establishes the quality-gate mindset. The refactoring step extends it with one bounded question:

> **Structural Review:** What improvements does this implementation reveal?
> - [ ] Identify any duplication or abstraction opportunities introduced by this feature
> - [ ] Note any renames, extractions, or reorganizations that would improve clarity
> - [ ] If identified: implement as separate `refactor:` commits with all tests still passing
> - [ ] If none: explicitly confirm scope is clean

---

## Sources

- Kent Beck, *Tidy First?* (2023) — structural/behavioral commit separation
- Kent Beck, *Refactoring* (1999) — Two Hats doctrine
- Martin Fowler, [Opportunistic Refactoring](https://martinfowler.com/bliki/OpportunisticRefactoring.html)
- Martin Fowler, [Preparatory Refactoring](https://martinfowler.com/articles/preparatory-refactoring-example.html)
- PeerJ controlled experiment: "The effects of change decomposition on code review" — 28 subjects, tangled vs. separated PRs
- ScienceDirect empirical study: "Deciphering refactoring branch dynamics" (Qt project)
- arxiv 2508.11126 — AI Agentic Programming: A Survey (scope creep as documented failure mode)
- arxiv 2511.04427 — Speed at the Cost of Quality (agentic session quality degradation)
- LoCoBench (2025) — context window performance degradation in long-context LLM sessions

---

## License & Attribution

This document is part of the Human-AI PDCA Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-framework)

---
*2026*
