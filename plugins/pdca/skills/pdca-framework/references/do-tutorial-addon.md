---

# Tutorial: DO Phase (Optional)

**If tutorial mode is on** (see `tutorial-setup.md`), open your first reply in this phase with
the line `Tutorial mode: on (DO)`, then weave in — briefly, don't pad the actual DO output — what
follows. This is first-reply-only: don't repeat it on every turn within the same phase.

**What this phase is:** strict TDD execution, one plan step at a time. Before every test: a
Called Shot (test name, behavior under test, expected failure, why this test first, a stub
check, and an independent oracle) — no exceptions. Red first, then minimal code to pass
(green), then commit before the next red.

**How to use it:** invoke this phase once per plan step from PLAN, not once for the whole plan.
Intervene immediately if the agent writes code before a failing test, or writes more than the
plan step calls for.

**What's next:** you (not the agent) decide when all plan steps are done. Open CHECK with
`/pdca:check` (marketplace install), `/pdca-check` (manual install), or `@pdca-framework`
(claude.ai/Codex) once implementation is complete.

Full walkthrough: [CHEATSHEET.md](https://github.com/kenjudy/pdca-agentic-coding-framework/blob/main/CHEATSHEET.md).
