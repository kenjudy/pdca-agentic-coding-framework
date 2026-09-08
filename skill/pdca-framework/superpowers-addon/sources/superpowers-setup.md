# Superpowers Setup Guide

> Load this only when setting up superpowers interop for the first time.

**Optional Enhancement**: [superpowers](https://github.com/obra/superpowers) is a skills
library for coding agents — brainstorming, systematic debugging, code review, worktrees,
parallel agents, plan writing and execution.

> **Prerequisite:** This addon assumes superpowers is already installed and active. If the
> `superpowers:using-superpowers` skill is not present in this session, the precedence
> guidance in `superpowers-workflow.md` governs nothing.

## Installing Superpowers

Install and configuration instructions live upstream and change independently of PDCA —
see [github.com/obra/superpowers](https://github.com/obra/superpowers) for current steps.
Do not follow stale copy-pasted instructions from elsewhere; use the upstream README.

## There Is No Partial Install

Unlike beads (a CLI you call) or ponytail (a command you invoke), superpowers installs a
`SessionStart` hook that injects its dispatcher skill into every session, clear, and
compact. That dispatcher states that if a skill applies, using it is not optional.

There is no supported way to take some skills and not the dispatcher — the only documented
opt-out in the upstream repository is for telemetry. So the question is never *whether*
superpowers is active; if it is installed, it is active. The question is which framework
governs where they overlap, and superpowers answers that itself:

> "User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take
> precedence over skills."

That clause is what `superpowers-workflow.md` rests on. It is upstream's own rule, not a
workaround: PDCA does not intercept skill dispatch, patch settings files, or vendor copies
of upstream skills.

## Liveness Check

Ask the agent which skills it has available, or check whether it announces
"Using superpowers:… " when starting work. If superpowers never announces a skill, it is
not active — install it first, or proceed without this addon.

---

## License & Attribution

**License:** superpowers is MIT licensed, © Jesse Vincent. This addon references
superpowers' behavior; it does not vendor or redistribute superpowers' skills, code, or
install instructions.

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-agentic-coding-framework)
