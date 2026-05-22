# Implementation Phase: TDD Execution

**Purpose:** Execute planned changes using strict Test-Driven Development discipline
**When to use:** After completing planning phase, for each implementation step
**Prerequisites:** Detailed implementation plan with atomic steps defined
**Expected output:** Working, tested code changes following red-green-refactor cycle
**Typical duration:** Variable (15 minutes to several hours depending on scope)
**Next step:** Completeness check (3) when all planned steps complete
**Critical:** Human must intervene immediately when TDD discipline breaks

If possible, rather than trigger a build, switch to agent mode and use this prompt to provide guidance to the build.

> **Tool check:** Is there a Claude Code command to show you what has already changed, to confirm your baseline before writing any new code? (e.g., `/diff`)

<!-- CLAUDE_INJECT: do-think-probe -->

---
```markdown

Try to add tests to existing fixtures where the tests fit coherently into the concerns of that fixture rather than proliferate new test files.

  **🚨 BEFORE STARTING STEP - ARCHITECTURAL SAFETY CHECK 🚨**
  - [ ] Creating new files? Run `Glob **/[area]*` - does module/package/namespace fit conceptually?
  - [ ] Modifying existing code? Run `Grep <class/function>` - if >2 usages, justify why modify vs. adapt
  - [ ] Moving files? Use `git mv` (not `mv`) to preserve history
  - [ ] Present file locations + modifications to user for approval BEFORE writing code

**TDD Implementation**

1. ❌ DON'T test interfaces - test concrete implementations
2. ❌ DON'T use compilation errors as RED phase - use behavioral failures
3. ✅ DO create stub implementations that compile but fail behaviorally
4. ✅ DO use real components over mocks when possible

   THIS MEANS: Compilation errors are not a valid red. A red test is when an invocation does not meet the expectation. So, that would imply the project can compile and the method stubs exist but the behavior is not fully implemented.

**🚨 CALLED SHOT — MANDATORY BEFORE EVERY TEST 🚨**

YOU MUST output all four before writing or running any test:
- **Test name:** [descriptive name]
- **Behavior under test:** [the observable behavior this verifies]
- **Expected failure:** [exact assertion message or error expected when the test runs red]
- **Why this test first:** [why this is the most conditionally interesting test to write next, or for degenerate/zero cases, why this establishes the API before anything else]

Run the test. If actual failure ≠ expected failure — STOP. Diagnose the mismatch before writing any production code. A test that fails differently than predicted is testing the wrong thing.

**Test Sequencing**

Work through behaviors in this order:
1. **Degenerate/zero case first** — empty state, null input, no items (establishes the API)
2. **1-2 exception cases** — invalid input, error conditions (defines the valid input contract before core logic)
3. **Happy path incrementally** — simplest case first (Fake It), then generalize (Obvious Implementation)
4. **Remaining exception cases** — those that require the established core to be meaningful

Never stop with only happy path coverage. All cases must be on the test list from the start.

If the next test in sequence would pass trivially against the current stub (vacuous green), skip to the first test the stub cannot satisfy — that is the genuine RED. See `references/testing-anti-patterns.md` #7.

**Stub Design**

Stubs return hardcoded plausible values -- never conditional logic. If making a test GREEN requires adding an `if` or `switch` to the stub, the stub has grown into an implementation. Delete the conditional, re-stub, and choose a more targeted test.

*(Principle: "Hardcode if possible, don't make it handle future scenarios." -- [afbreilyn/afb-tdd](https://github.com/afbreilyn/afb-tdd))*

**Test Selection When Conditionals Exist**

When the feature includes conditional branches (e.g., `if confidence < threshold, set escalate flag`), the first test must target those branches -- not the happy path.

*Ask:* "If I implemented only the happy path with no conditionals, would this test pass?" If yes, it is the wrong first test. Writing it first forces the stub to grow into a full conditional implementation, making subsequent conditional-branch tests vacuously green before they are written. See `references/testing-anti-patterns.md` #7.

**If beads is active** (a beads issue is assigned for this TDD step), record the ordering decision before writing the first test:

```bash
bd update [task-id] --append-notes "$(cat <<'EOF'
TDD ordering: [conditional branch test name] before [happy-path test name]
Reason: happy-path first risks implementing full conditional in one GREEN step,
making conditional-branch tests vacuously green.
EOF
)"
```

This note survives context compaction. `bd show [task-id]` recovers it before writing a GREEN phase.

**Test Scope — Which Level?**

| Question | → |
|---|---|
| Can this behavior be verified without external dependencies? | Unit test |
| Does it verify serialization, deserialization, or a system boundary? | Narrow integration test |
| Is it a critical user journey not covered at a lower level? | E2E test |
| Is it already covered at a lower level? | Don't duplicate it |

Mock only at infrastructure boundaries (external services, filesystem, database). Do not mock internal collaborators — tests that mock internals break on refactoring and test implementation, not behavior.

**When Unit Tests Can't Replicate Production Bugs:**
If production evidence (logs, metrics) proves a bug exists but unit tests pass:
- **Diagnosis:** Testing at wrong scope — unit test fixtures too small to trigger scale-dependent behavior
- **Preferred:** Write integration test with realistic data scale (accept slower execution)
- **Acceptable:** Write unit-level regression test AND document production evidence in test comments
- **Anti-pattern:** Never call it RED phase if the test passes — be honest it's a regression test
- **Required:** Commit message must include production metrics showing bug before/after
    
**AI Command Transparency:**

- [ ] Show reasoning, particularly when you need to deviate from plan.

**Current step:** 
**Red phase:** Write the failing test first (NO exceptions)
**Green phase:** Make it pass with minimal code — then commit before moving to the next RED
**Refactor:** Clean up if needed

**Test Complexity Management:**
- Start with single-file, basic scenarios
- Avoid multi-file compilations initially
- If test setup gets complex, simplify the scenario
- Build complexity gradually in subsequent iterations

**Ready for commit?**
- [ ] Test written and failing first ✅
- [ ] Implementation makes test pass ✅
- [ ] Code is clean ✅
- [ ] TDD discipline maintained ✅
- [ ] Linting passes (check githooks, makefile, or package.json/project files for configured tools) ✅
- [ ] Compilation/build succeeds ✅
- [ ] All quality gates pass (type checks, format checks, etc.) ✅
- [ ] Commit message ready

**Next:** What's the next smallest testable piece?
																	**⚠️ Process Police Alert:** User should intervene if TDD discipline breaks!

⚠️ **STOP**: Do not declare "complete" or "done". Say
  "Implementation finished, moving to CHECK phase."													
```


> **Tool check:** Before committing, is there a Claude Code command to review what changed? (e.g., `/diff`) One to check code quality? (e.g., `/simplify`) If this step touches auth or data, one to catch security issues? (e.g., `/security-review`) Is context getting long and losing focus? (e.g., `/context`, `/compact`)

If you notice the agent making changes without test driving, making sprawling edits, or otherwise breaking the rules of engagement then the model has lost context and you need to stop it and reign it back in.

Stop the thread. Tell it what you observe happening. Repost the 3 prompts. Tell it to proceed.


---

## License & Attribution

This template is part of the Human-AI PDCA Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Usage:** You are free to use, modify, and distribute this template with appropriate attribution. 

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-framework)

---
*2025*
