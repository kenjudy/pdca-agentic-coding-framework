# PDCA Cheat Sheet

One page. Full prompts live in `skill/pdca-framework/references/` (or `1. Plan/` – `4. Act/` in this
source repo). Full context: `skill/pdca-framework/SKILL.md`.

## Before you start

Can you finish this sentence? **"After this session, ___."**
If not, write it now — an unstated goal makes CHECK and ACT untestable.

## The cycle

| Phase | Duration | Use when | Output |
|---|---|---|---|
| **1. PLAN** | 7–15 min | Starting new/unclear work; multiple approaches possible | Approach + numbered implementation steps |
| **2. DO** | 15 min – hrs | After planning, once per step; restart on context drift | Working, tested code (red-green-refactor) |
| **3. CHECK** | 2–5 min | All planned steps done; before committing; when unsure if finished | Verification + process audit + Status/Ready-to-close verdict |
| **4. ACT** | 5–10 min | End of every session, success or not | Critical moments, insights, working-agreement updates |

Do NOT skip CHECK/ACT to save time — that's the exact failure mode this framework exists to prevent.

## PLAN

1. **Analyze first** (1a): search the codebase for similar patterns before proposing anything — do not
   invent an approach with no codebase evidence.
2. **Plan second** (1b): numbered, atomic, testable steps. One behavior per step. List preparatory
   refactoring separately, before feature steps.
3. New skill/build artifact? Name explicit tasks for build system, docs, CHECK criteria, and ACT
   retro in the plan — don't assume them.

## DO — one step at a time

**Called shot — mandatory before every test, no exceptions:**
```
Test name:          [descriptive name]
Behavior under test: [observable behavior this verifies]
Expected failure:    [exact assertion/error expected when it runs red]
Why this test first: [most conditionally interesting next, or why it establishes the API]
```
Then: write the failing test → confirm it's RED for the right reason (not a compile error) →
write the minimum code to pass → refactor → next test.

**Stub discipline:** a stub returns hardcoded values, never conditional logic. When the feature has
branches, the first test targets a branch, not the happy path — starting with the happy path lets
later tests pass vacuously before they're written.

Never declare the work finished mid-DO. Hand off with: *"Implementation finished, moving to CHECK
phase."*

## CHECK

```
Verification:        all tests passing (show output) · smoke test · docs updated · no regressions ·
                      no leftover TODOs
Process Audit:        TDD discipline held · no untested implementation committed (show diff) ·
                      adversarial critic pass run if multi-file or end-to-end claim
Structural Review:    improvements found during DO only — no speculative cleanup
Status:               [Complete / Needs work]
Ready to close:       [Yes/No + reasoning]
```
A passing build is necessary, not sufficient. Don't certify Complete on unresolved items.

## ACT

Factual summary → open question (don't interpret for the human) → hypotheses, not verdicts → ask
for ONE thing to change → offer to save (beads note / working agreement / skip).

## Working agreements (non-negotiable)

**Intervene immediately** on a process violation — stop and answer before continuing:
- "You broke from test-driving. Is there adequate test coverage?"
- "Where's the failing test first?"
- "You're fixing multiple things. Focus on one failing test."
- "This feels like scope creep. Are we still on step [N]?"

**Implementation guidelines:**
1. Smallest change that addresses the issue
2. One focused change, one failing test, at a time
3. Work within existing architecture — no drive-by rewrites
4. Read the test before assuming what it wants
5. Understand a component before changing it
6. Treat widely-called methods with extra caution
7. Consider side effects on the rest of the codebase
8. A broken test means try a different approach, not patch the patch
9. Explain the rationale for the approach chosen
10. Use precise, domain-correct terminology

## If it goes off the rails

1. Stop the thread immediately
2. Describe what you're observing
3. Repost the relevant phase prompt
4. Redirect and resume

## Validating a prompt/rubric change

Never trust a single eval run — scenarios fail on unmodified text too. Always interleave
control/treatment and read the Fisher p-value, never two raw pass rates. See `CLAUDE.md`.
