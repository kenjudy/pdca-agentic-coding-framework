# Testing Anti-Patterns Reference

> Adapted from [obra/superpowers](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)
> Copyright (c) 2025 Jesse Vincent. MIT License.
> Adapted for the PDCA Framework by Ken Judy.

Core principle: **Test what the code does, not what the mocks do.**

---

## 1. Testing Mock Behavior

Verifying that a mock was called rather than that the system behaved correctly. If your assertion is checking a mock expectation rather than an observable outcome, delete it.

*Ask yourself:* "Am I testing the behavior of a mock?" If yes — remove the assertion or stop mocking.

---

## 2. Mocking Without Understanding

Adding mocks based on assumptions about what a dependency does, before running the real implementation. This produces tests that pass even when the assumption is wrong.

*Rule:* Run tests with real implementations first to understand actual behavior. Add mocks only at confirmed infrastructure boundaries (external services, filesystem, database, clock).

---

## 3. Incomplete Mocks

Returning only the fields your current test needs from a mock response. When the production code path changes, incomplete mocks silently mask regressions.

*Rule:* Mirror the complete real API response shape — not just the fields you're asserting on right now.

---

## 4. Test-Only Methods in Production Code

Adding public methods or hooks solely for test cleanup or inspection pollutes the production API.

*Rule:* Move any test-only behavior into dedicated test utilities. If you find yourself adding a method "just for tests," stop and restructure.

---

## 5. Tests Written After Code

Tests written after implementation answer "What does this do?" Tests written first answer "What should this do?" Only tests-first catch the wrong design early.

*Consequence:* Tests that pass immediately after being written prove nothing. If your test never failed, you don't know it tests the right thing.

---

## 6. Integration Tests as Afterthought

Treating integration coverage as optional cleanup after unit tests are written misses the boundary behaviors that matter most.

*Rule:* Integration tests belong in the test sequence from the start — include them in the test list during planning (Phase 1b), not after the fact.

---

## 7. Vacuous Greens

A test that passes immediately against the current stub without any production code change. Vacuous greens feel like progress but provide no genuine RED phase — you cannot know the test is testing the right thing.

*Diagnosis:* If the next test in sequence would pass trivially against the current stub, it is a vacuous green.

*Rule:* Skip to the first test in your sequence that the current stub cannot satisfy — that is your genuine RED. Document the skipped tests as guards to add after real implementation replaces the stub. State the called shot for the test you are actually going to write, not the one you are skipping.

**Sub-case: Ordering-Triggered Vacuous Green**

Starting with the happy-path test can force the stub to grow into a full implementation, making all subsequent conditional-branch tests vacuously green. Symptom: test #2 passes immediately because test #1 already required implementing the conditional logic.

*Ask before choosing the first test:* "If I implemented only the happy path with no conditionals, would this test pass?" If yes, choose a different first test -- one that targets the conditional branch.

*Prevention:* When the feature includes conditional branches, start with the test that isolates the most conditional behavior. The happy-path test written after a genuine RED/GREEN cycle is documentation; written first, it is a trap.

*Persistent context:* In longer DO phase sessions, record the ordering decision in beads task notes at the start so it survives context compaction. `bd show [task-id]` recovers the decision before writing a GREEN phase.

*Attribution: Anti-Pattern #7 (Happy-Path Tunnel Vision) from [afbreilyn/afb-tdd](https://github.com/afbreilyn/afb-tdd) -- "for every happy-path test, ask what are all the ways this can fail and write a test for each answer."*

---

## 8. Partial-Instance Coverage

Testing the first edited instance of a repeated assumption -- one step of a multi-step flow, one file of a documented multi-file change, one command of a multi-command sequence -- and treating the task as done, when the task's own acceptance criteria makes a whole-flow or whole-file claim ("operator can run X end-to-end," "stage Y now supports Z").

*Diagnosis:* The acceptance criteria's claim is broader than what the tests actually exercise. Each individual test passes; the claim the criteria makes has never been tested as a whole.

*Rule:* Before closing, grep the full scope named in the acceptance criteria for every other instance of the assumption just removed or changed -- not just the one instance you edited. If the plan describes a multi-step operator flow (e.g., run command A, then conditionally run command B), write a test that exercises the full sequence, not just each command in isolation.

*Origin:* Found via adversarial review after a fix shipped that added a mode-override flag but tested only the single-command cases (set mode, auto-detect mode, explicit-flag-overrides-detection) -- never the two-command sequence (detect, then re-run to override) the design actually specified. A sibling fix split a multi-step file's Step 1 for two modes, tested Step 1, and closed the task -- Steps 2-6 of the same file still assumed the removed constraint. Both were caught by a fresh critic reading the whole file/flow, not by the tests written during Do.

*This rule does not self-apply.* On the very next cycle after it was written, the identical pattern recurred twice more (a docs pass that fixed only the first mention of a stale claim, not the rest of the document; a stage file's own overview sentence left unconverted because it sat outside any labeled per-mode section) -- caught again only by a fresh adversarial pass, not by re-reading this list. Advisory text you wrote for yourself is not a gate; see the Check phase's Decision probe, which now requires an operator-chosen critic model rather than relying on the same session re-reading its own work.

---

## Quick Check Before Committing

- [ ] Every assertion is on real behavior, not mock call counts
- [ ] Mocks exist only at infrastructure boundaries
- [ ] Mock responses mirror the full real API shape
- [ ] No production methods exist solely for test access
- [ ] Every test watched fail before watching it pass
- [ ] If the acceptance criteria makes a whole-flow/whole-file claim, a test exercises the complete thing -- not just the edited piece (see #8)
