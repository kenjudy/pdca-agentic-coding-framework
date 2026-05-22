# Human Working Agreements: Collaboration Contract

**Purpose:** Define non-negotiable process discipline and intervention protocols
**When to use:** Reference throughout all phases, update based on retrospective learnings
**Prerequisites:** None - this is the foundational document
**Expected output:** Clear behavioral expectations for both human and AI participants
**Update frequency:** After retrospectives that identify process improvements
**Critical:** These agreements override immediate progress in favor of process integrity

---
## **Process Discipline & Intervention**
**USE TDD FOR CHANGES.** I will interrupt immediately with direct questions when I observe process violations:
- "You broke from test-driving. Is there adequate test coverage?"
- "Where's the failing test first?"
- "You're fixing multiple things. Focus on one failing test?"
- "This feels like scope creep. Are we still on step [N]?"

**You must:** Stop and answer the process question before continuing. Process discipline trumps immediate progress.

## **Implementation Guidelines**

1. **PRIORITIZE MINIMAL CHANGES:** Smallest possible change addressing the specific issue. Specialized edge case handling over core method modification.

2. **INCREMENTAL APPROACH:** One focused change at a time. One failing test at a time, no exceptions.

3. **RESPECT EXISTING ARCHITECTURE:** Work within established patterns. No dramatic approach changes unless requested.

4. **VERIFY TEST EXPECTATIONS:** Examine test cases first to understand expected behavior. No assumptions about requirements.

5. **UNDERSTAND BEFORE CHANGING:** Read enough codebase to understand component interactions before modifications.

6. **BE CAUTIOUS WITH CORE METHODS:** Methods called from many places have multiple behavioral expectations.

7. **CONSIDER SIDE EFFECTS:** How changes affect other codebase parts and test cases.

8. **RESPOND TO FEEDBACK:** If changes break tests, try different approach rather than fixing the fix.

9. **EXPLAIN RATIONALE:** Clear explanations for approach choices and trade-offs considered.

10. **USE CLEAR TERMINOLOGY:** Precise technical language matching the domain.

---

## License & Attribution

This document is part of the Human-AI TDD Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Living Document:** These working agreements should be continuously refined based on retrospective learnings from each collaboration session.

**Source:** [Human-AI Collaboration Process Repository](https://github.com/kenjudy/pdca-framework)

---
*2025*