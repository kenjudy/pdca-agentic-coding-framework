# TDD Research: Test Ordering and Scope Decision Criteria

**Purpose:** Reference for improving TDD guidance in the PDCA framework
**Research date:** 2026-03-20
**Related issue:** [#6 — Rework TDD description](https://github.com/kenjudy/pdca-agentic-coding-framework/issues/6)

---

## Golden Path vs. Exception Path — What Order?

There is a genuine debate in the literature. Both positions have merit, and they converge on the key points.

### Position 1 — Exceptions First (Robert C. Martin, "Thorns Around the Gold")

The "Gold" is core happy-path functionality, surrounded by an invisible hedge of thorns — exception conditions, degenerate inputs, ancillary behaviors. Grabbing directly for the Gold entangles you.

**Martin's prescribed order** (after 15 years of TDD practice):
1. **Exceptional behaviors** — invalid inputs, error conditions, semantic violations
2. **Degenerate behaviors** — inputs that cause core logic to do "nothing" (empty string, zero-length collection)
3. **Ancillary behaviors** — supporting functions that serve core logic
4. **Core functionality (the Gold)** — only after the above are cleared

**Why:** Exception cases define the error contract before you write the happy path. You discover the shape of valid vs. invalid input before committing to core logic implementation.

### Position 2 — Zero/One/Many First (James Grenning, ZOMBIES; Kent Beck, TDD by Example)

ZOMBIES is a mnemonic for "what test do I write next?":

| Letter | Meaning | When |
|---|---|---|
| **Z** | Zero | First: empty/initial state. Establishes the API. |
| **O** | One | Second: single item/first transition. Establishes lower boundary. |
| **M** | Many (More complex) | Third: generalization. Forces the general case. |
| **B** | Boundary behaviors | Throughout: state transitions, edge values. |
| **I** | Interface definition | As you go: tests drive API design. |
| **E** | Exercise exceptional behavior | After core behavior is established. |
| **S** | Simple Scenarios, Simple Solutions | Always: minimal production code per test. |

Beck's "Starter Test" principle: pick the test that is most obviously doable — often a degenerate case — to clarify the API before investing in real implementation. The test list (including exceptions) is built upfront; the ordering is a judgment call.

### Where the Positions Converge

Both agree on:
- All cases (golden and exceptional) belong on the to-do list from the start — this is behavioral analysis before implementation
- The **zero/degenerate case** comes first (empty state, null input, no items). Martin calls it a "thorn"; Grenning calls it "Z". Same test, different framing.
- Core functionality is **not** the very first test
- Never stop at happy path alone — complete coverage requires both

**The practical synthesis:**
1. Start with the zero/degenerate case
2. Write 1-2 exception cases to define the valid input contract before core logic
3. Build the happy path incrementally (Beck: Fake It → Obvious Implementation → Triangulate)
4. Return to remaining exception cases that depend on the now-established core
5. Done only when both paths are covered

The ZOMBIES "E" being last does not mean exceptions are afterthoughts — they are on the list from step 0. It means the exception tests that *require a working system* are written after the system exists.

---

## Unit vs. Integration vs. E2E — Decision Criteria

### The Central Insight (Ian Cooper, "TDD, Where Did It All Go Wrong")

The industry misread Beck's "unit test" to mean "test per class/method." Beck's actual definition: a test that runs **in isolation from other tests** — not isolation from collaborating code.

**Consequence of the misunderstanding:** Tests that know about every class and method in an implementation get baked to the implementation. Refactoring breaks these tests, undermining the very thing TDD is supposed to enable.

**Cooper's corrected model:**
- The unit of isolation is a **module** — one class, multiple collaborating classes, or a facade
- Test **behaviors** at the public API boundary of the module, not internal implementation details
- The trigger for a new test is a **new required behavior** — not a new method or class
- Mock only at **module/infrastructure boundaries** (external services, filesystem, database); not internal collaborators

**The test-level litmus:** If you can refactor internal implementation without changing any test, your tests are at the right level of abstraction. If internal refactoring breaks tests, the tests are too close to the implementation.

### Practical Decision Criteria (Martin Fowler, Practical Test Pyramid)

"Push your tests as far down the test pyramid as you can."

| Question | Answer → Test type |
|---|---|
| Can this behavior be verified without external dependencies? | Unit test (sociable or solitary) |
| Does this verify serialization/deserialization or the boundary to an external system? | Narrow integration test |
| Is this a critical user journey not covered at a lower level? | E2E test |
| Is this scenario already covered below? | Do not duplicate it at a higher level |

**Feathers' operational proxy** (Working Effectively with Legacy Code): If the test talks to a database, network, or filesystem — it is not a unit test, regardless of what you call it. Speed and determinism are the practical consequences of the isolation requirement.

**Sociable vs. Solitary tests** (Jay Fields, via Fowler): Use real collaborating objects by default (sociable). Use test doubles only when collaboration is "awkward" — external service, non-deterministic, slow. This aligns with Cooper: mocking internal collaborators produces implementation-coupled tests.

### Narrow vs. Broad Integration Tests (Fowler)

- **Narrow:** Test doubles replace external services; fast; appropriate in the deployment pipeline
- **Broad:** Live versions of all services; slow; appropriate only as final smoke tests

Prefer narrow integration tests. Broad tests are a diagnostic tool, not a development workflow.

### Fowler's Failure-Propagation Rule

A failing integration or E2E test with no corresponding failing unit test reveals a **gap in the unit test suite** — fix the unit test first, then fix the code. The integration test discovered the gap; a unit test should own it going forward.

### When to Break the Pyramid

- When integration or E2E tests become fast and cheap (e.g., in-process SQLite, contract tests). Fowler: "If my high level tests are fast, reliable, and cheap to modify — then lower-level tests aren't needed."
- When the behavior is inherently about the integration (ORM mapper, serialization boundary, network protocol). Fowler: "Write integration tests for all pieces of code where you either serialize or deserialize data."
- When working with legacy code without tests (Feathers): write **characterization tests** at whatever level gives you a seam, then work toward unit coverage.

### TCR's Mechanical Constraint (Kent Beck)

`test && commit || revert` makes one thing non-negotiable: inner-loop tests must be fast enough to run after every change. Slow integration tests belong outside the TDD inner loop — run them in CI, not at every save.

---

## Key Sources

| Author | Source | Key Contribution |
|---|---|---|
| Kent Beck | *TDD by Example* (2002) | Starter tests, Fake It/Obvious/Triangulate, test to-do list |
| Kent Beck | "Canon TDD" (2023, Substack) | Behavioral analysis before implementation; test ordering as skill |
| Kent Beck | "test && commit || revert" (2018) | Inner-loop tests must be fast; micro-increments |
| Kent Beck | "Test Desiderata" | 12 test properties; structure-insensitive as a goal |
| Robert C. Martin | "Thorns Around the Gold" (2014) | Exception-first ordering; define error contract before core logic |
| Robert C. Martin | "The Cycles of TDD" (2014) | Three Laws at nano-cycle; code generality grows with test specificity |
| Ian Cooper | "TDD, Where Did It All Go Wrong" (talk) | Unit = isolation from other tests, not collaborators; behavioral boundaries |
| James Grenning | "TDD Guided by ZOMBIES" | ZOMBIES mnemonic for test sequencing |
| Martin Fowler | Practical Test Pyramid | Push tests down the pyramid; decision criteria; failure-propagation rule |
| Martin Fowler | Unit Test, Integration Test (bliki) | Sociable vs. solitary; narrow vs. broad integration |
| Michael Feathers | *Working Effectively with Legacy Code* (2004) | Operational proxy for unit tests; characterization tests; seams |

---

*Research conducted for PDCA Process framework improvement. Do not plagiarize — use as a basis for original guidance.*
