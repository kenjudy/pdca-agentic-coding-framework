---

# Autonomous CHECK Critic Setup (Optional)

**First-time setup only.** If you want the CHECK phase's autonomous-mode critic fallback (see
`3. Check/3. Completeness Check.md` and `references/check-autonomous-critic-addon.md`) to use a
specific review skill or model rather than the default fallback, declare it once in your
project's `CLAUDE.md`:

```markdown
## PDCA Autonomous CHECK Critic
- Review skill: <name, or "fresh subagent only">
- Model: <explicit model id, or "default tier table">
```

No section, or a section that sets only one of the two lines, is fine — the unset one uses the
default: fresh subagent only, model chosen from the tier table in
`references/check-autonomous-critic-addon.md`.

This declaration is read only when the session is operating autonomously (no operator present
to answer the HITL decision probe). In a human-in-the-loop session, the operator is always
asked directly instead, and this file is never consulted.
