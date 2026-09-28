# Check Phase: Implementation Verification & Quality Audit

**Purpose:** Verify all objectives met and process discipline maintained
**When to use:** After completing all planned implementation steps
**Prerequisites:** All planned work completed, tests passing
**Expected output:** Verification checklist, process audit results, outstanding items list
**Typical duration:** 2-5 minutes
**Next step:** Retrospection (4) for continuous improvement

---

> **Tool check:** Before running this check, is there a Claude Code command to see all uncommitted changes? (e.g., `/diff`)

**Decision probe (30 sec):**

- Did the implementation reveal anything the plan did not anticipate — new dependencies, structural issues, or scope changes? → if yes: flag the specific finding for the ACT retrospective before closing
- Does the changed code touch auth, data persistence, or external APIs? → if yes: run `/security-review` before committing
- Does this change span more than one file, or does its acceptance criteria include an end-to-end/completeness claim? → if yes: before presenting CHECK results, run an adversarial critic pass with a fresh subagent. Ask the operator which model to use (e.g. a higher-tier model than Do used, or a model built for critique) rather than defaulting to one silently. Brief the critic to read the actual current files and diff itself rather than trust this session's own summary — see `references/testing-anti-patterns.md` #8, which this practice exists to enforce (the anti-pattern's own text is advisory and does not self-apply; a fresh adversarial read is what has actually caught its recurrences).

```
**Completeness Check**

Review our original goal outcome and plan against our execution.

**Verification:**
- [ ] All tests passing
- [ ] Manual smoke test completed successfully 
- [ ] Documentation updated
- [ ] No regressions introduced
- [ ] No TODO implementations remaining created by this test driving
  - *If ponytail is active:* `# ponytail:` markers count here — run `/ponytail-debt` and record each under **Outstanding items**. A marker left over untested logic is an unfinished implementation and blocks close.

**Process Audit:**
- [ ] Testing approach was followed consistently
- [ ] TDD discipline maintained (if chosen)
- [ ] Test coverage is adequate and appropriate
- [ ] No untested implementation was committed
- [ ] Simple test scenarios were effective
- [ ] For any acceptance criteria with an end-to-end/completeness claim, or any change spanning more than one file, was an adversarial critic pass run with a fresh subagent, model chosen by the operator, asked which tests would still pass if the implementation were subtly wrong? (see `references/testing-anti-patterns.md` #8, #10; a self-review or re-read by the same session that did the work is not a substitute — it is exactly what has repeatedly missed these findings)
  - *If operating autonomously* (no operator to ask): don't pause — follow the review skill and model declared in `references/autonomous-critic-setup.md`, or fall back to a fresh subagent with no third-party skill on a different model than the one doing the work. See `references/check-autonomous-critic-addon.md` for this environment's mechanics, if it has one.


**Structural Review:**
- [ ] What structural improvements did this implementation reveal? (discovered during Do only — no speculative cleanup)
- [ ] If identified: implement as separate `refactor:` commits with all tests still passing
- [ ] If none: confirm scope is structurally clean

**Status:** [Complete/Needs work]
**Outstanding items:** [any remaining tasks]
**Ready to close:** [Yes/No with reasoning]

```

> **Tool check:** Is there a Claude Code tool to surface code quality improvements in what changed? (e.g., `/simplify`, or `/ponytail-review` if ponytail is installed) One to catch security concerns? (e.g., `/security-review`)

Add Results to Ticket.


---

