---

# Tutorial: PLAN Phase (Optional)

**If tutorial mode is on** (see `tutorial-setup.md`), open your first reply in this phase with
the line `Tutorial mode: on (PLAN)`, then weave in — briefly, don't pad the actual PLAN output —
what follows. This is first-reply-only: don't repeat it on every turn within the same phase.

**What this phase is:** PLAN has two sequential sub-steps, run in order:
- **1a. Analysis** — understand the problem, discover existing patterns in the codebase, assess
  complexity. Mandatory before any approach is chosen.
- **1b. Detailed Planning** — only after 1a is done. Turn the chosen approach into numbered,
  atomic implementation steps with a testing strategy and acceptance criteria.

**How to use it:** describe the goal in plain language; the agent runs 1a first, then 1b. If a
step in the resulting plan feels too large to test atomically, say so — it should be split
before you move on.

**What's next:** once you approve the plan, you (not the agent) start the next phase when
you're ready — this phase does not continue into it on its own. Open DO with `/pdca:do`
(marketplace install), `/pdca-do` (manual install), or `@pdca-framework` (claude.ai/Codex).

Full walkthrough: [CHEATSHEET.md](https://github.com/kenjudy/pdca-agentic-coding-framework/blob/main/CHEATSHEET.md).
