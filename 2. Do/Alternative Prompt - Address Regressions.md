# Regression Handling: Systematic Test Failure Resolution

**Purpose:** Address multiple test failures potentially caused by recent changes
**When to use:** When test suite shows multiple failures after code changes
**Prerequisites:** Failing test suite with suspected regression causes
**Expected output:** All tests passing with clear understanding of what changed
**Typical duration:** 1-3 hours depending on failure scope
**Next step:** Completeness check (3) to ensure no further regressions
**Critical:** Don't change production code and test expectations simultaneously

---
```markdown
We have failing tests in [Reference Test Fixture]. These failures may be due to recent changes that introduced regressions. 

**Regression Analysis First:**
- Analyze ALL failing tests together before starting fixes to identify common patterns
- Understand what changed in the production code that caused these failures
- Determine if tests expect old behavior or if production behavior changed intentionally

**Change Discipline:**
Be careful not to change both production code and test expectations in one pass as that might change behavior. So, you are free to adjust test setup. But stop and ask permission to change production code or expectations. So that we can agree on the changes. 

**Batch Processing:**
- When you identify a common pattern across multiple failing tests, propose batching similar fixes
- Apply TDD discipline: one test or logical batch at a time, red/green/refactor

**Validation:**
When a broken test goes green, re-run the fixture to ensure no further regressions.

**Focus Areas:**
- Implementation details vs. behavior: Are tests failing due to logging levels, error messages, or actual behavior changes?
- Configuration thresholds: Are failures due to environment-specific settings (timeouts, limits, etc.)?
- Expected failure modes: Do tests expect certain exceptions/failures that no longer occur?
```


---

## License & Attribution

This template is part of the Human-AI TDD Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Usage:** You are free to use, modify, and distribute this template with appropriate attribution. 

**Source:** [Human-AI Collaboration Process Repository](https://github.com/kenjudy/pdca-framework)

---
*2025*