---

# Tutorial: CHECK Phase (Optional)

**If tutorial mode is on** (see `tutorial-setup.md`), open your first reply in this phase with
the line `Tutorial mode: on (CHECK)`, then weave in — briefly, don't pad the actual CHECK output —
what follows. This is first-reply-only: don't repeat it on every turn within the same phase.

**What this phase is:** a completeness check against PLAN's acceptance criteria and the
process itself — all tests passing, no untested implementation, TDD discipline maintained
throughout. For any end-to-end or completeness claim, or any change spanning more than one
file, an adversarial critic pass (a fresh subagent, model of your choice) belongs here too.

**How to use it:** invoke this phase once, after all of DO's plan steps are complete — not
per step. Answer its checklist honestly; a "yes" you can't point to evidence for isn't a yes.

**What's next:** you (not the agent) decide the cycle is verified. Open ACT with `/pdca:act`
(marketplace install), `/pdca-act` (manual install), or `@pdca-framework` (claude.ai/Codex)
for the retrospective.

Full walkthrough: [CHEATSHEET.md](https://github.com/kenjudy/pdca-agentic-coding-framework/blob/main/CHEATSHEET.md).
