# Superpowers Workflow Reference

> Load this during active PDCA sessions when superpowers is installed.

> **Prerequisite:** This addon assumes superpowers is installed and active. If it never
> announces a skill, it is not active — see `superpowers-setup.md`.

## Precedence

One rule, and it is upstream's own:

> "User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take
> precedence over skills." — `superpowers:using-superpowers`

**PDCA governs when work is verified and when it is finished. Superpowers governs how many
individual tasks are carried out.** Where a superpowers skill and a PDCA phase describe the
same ground, the phase prompt in front of you wins; everything else in superpowers applies
unchanged.

That is the whole rule. It is deliberately not a list.

> **Why there is no list.** Three specific conflicts were hypothesised before this addon
> was written — that superpowers' `finishing-a-development-branch` menu would end a branch
> without ACT, that its test-driven-development skill would drop the called shot, and that
> its verification-before-completion would be mistaken for CHECK. Each was measured against
> the *unmodified* phase masters. The first and third were refuted outright: the masters
> already refuse the merge and already decline to certify. The second was inconclusive.
> Writing precedence rules for conflicts that do not occur would have added text to three
> places to prevent nothing.

## Which Skills to Welcome

These fill genuine PDCA gaps. Nothing in the framework covers them, and they carry no
dependency on superpowers' process-routing skills:

| Skill | Why |
|---|---|
| `systematic-debugging` | PDCA has no debugging method. DO tells you to write a failing test; this tells you how to find what to test. |
| `using-git-worktrees` | Isolation for parallel work. No PDCA equivalent. |
| `requesting-code-review` | CHECK's tool-check probe asks whether a review tool exists; this is one. |
| `receiving-code-review` | How to act on review findings. PDCA stops at "add results to ticket". |
| `dispatching-parallel-agents` | PDCA's supervision protocol covers model selection, not fan-out. |
| `writing-skills` | Meta-work on skills themselves; orthogonal to a PDCA cycle. |

## Which Skills Defer to the Phase You Are In

These overlap a PDCA phase. Use whichever the human asked for, but when you are running a
PDCA phase, that phase's prompt is the instruction:

| Superpowers skill | Overlapping phase | What PDCA adds |
|---|---|---|
| `brainstorming` | PLAN 1a | Architecture pattern discovery and external system validation as blocking steps |
| `writing-plans` | PLAN 1b | Steps tagged for model selection; explicit build/docs/CHECK/ACT scope |
| `test-driven-development` | DO | The **called shot** — state the expected failure *before* writing the test, not after running it |
| `executing-plans` | DO | Per-step human confirmation rather than a run to completion |
| `verification-before-completion` | CHECK | Process audit, structural review, and human sign-off, beyond evidence-for-claims |

The TDD row is the one worth knowing. Superpowers' Iron Law is strong — no production code
without a failing test, and verify the RED — but it asks you to confirm the failure was
correct *after* running the test. PDCA asks you to predict it beforehand. The prediction is
what proves the test was capable of failing for the reason you think.

## Finishing a Branch

`superpowers:executing-plans` names `finishing-a-development-branch` a required sub-skill,
and it offers merge / PR / keep-as-is once tests are green.

Green tests are not a PDCA completion. Work is finished when CHECK and ACT have run and the
human has signed off. Take the menu after that, not instead of it.

---

## License & Attribution

**License:** superpowers is MIT licensed, © Jesse Vincent. This addon references
superpowers' behavior; it does not vendor or redistribute its skills or code.

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-agentic-coding-framework)
