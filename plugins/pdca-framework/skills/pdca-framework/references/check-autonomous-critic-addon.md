---

# Autonomous CHECK Critic Fallback — Claude Code Mechanics (Optional)

Concrete mechanics for the autonomous-mode fallback in `3. Check/3. Completeness Check.md`.
Only relevant when no operator is present to answer the HITL decision probe — in a
human-in-the-loop session, the operator is always asked directly instead, and this file is
never consulted.

## Model tier

| Working model | Critic model |
|---|---|
| Sonnet | Opus |
| Haiku | Sonnet |
| Opus (already the top tier) | A different model at the same tier — e.g. a fresh Opus session, not this one |

If the working model isn't in this table, treat the highest-reasoning model available in this
account as the top tier and apply the same rule. Freshness of context, not strictly higher
rank, is what makes the critic pass effective — see `references/testing-anti-patterns.md` #8 —
so a different model at the same tier is an acceptable ceiling, never the same session.

## Invoking the critic

Use the Agent tool with a fresh, non-continued context:

- **`subagent_type`**: the review skill declared in `references/autonomous-critic-setup.md`, if
  one is set; otherwise `general-purpose`.
- **`model`**: the tier chosen above, passed explicitly. Never omit it — an omitted model
  parameter typically inherits the calling session's model, which reproduces the exact
  self-review pattern #8 found doesn't catch these findings.
- **Prompt**: brief the critic to read the actual current files and diff itself, per
  `references/testing-anti-patterns.md` #8 — never summarize the change for it.
