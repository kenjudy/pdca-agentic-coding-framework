---

# Tutorial Mode Setup (Optional)

**First-time setup only.** Tutorial mode adds a brief explanation of the current phase — what
it is, how to use it, what comes next — to each PDCA phase's response. It is off by default.

## Turning it on

**Durable, for every session:** declare it once in your project's instructions file —
`CLAUDE.md` (Claude Code), `AGENTS.md` (Codex), or your claude.ai Project's custom
instructions:

```markdown
## PDCA Tutorial Mode
- Tutorial mode: on
```

This is read fresh each session (and by any subagent that loads project instructions), so it
survives context compaction, `/clear`, and a new session in a way an in-conversation statement
cannot.

**One-off, for a single phase invocation:** prefix your request with the literal phrase
`tutorial mode:` (or `tutorial mode off:` to suppress it for one call even when the project
declares it on):

```
/pdca:plan tutorial mode: add payment validation to checkout
```

A bare mention of the words "tutorial" or "mode" elsewhere in a request does not count — only
this exact leading prefix toggles it, so a task that happens to be about writing a tutorial is
never mistaken for a request to turn this addon on.

## Scope

Tutorial mode affects only replies addressed to the human operator. A subagent or an autonomous
CHECK critic that loads project instructions as background context does not add tutorial
explanations to its own output — the operator never reads a subagent's internal handback as a
teaching surface, and the four phase addon files are instructions for the top-level session
only.

No section in your project instructions, or an absent one, is fine — the default is off.
