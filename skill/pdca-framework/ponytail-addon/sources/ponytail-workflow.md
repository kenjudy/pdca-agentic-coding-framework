# Ponytail Workflow Reference

> Load this during active PDCA sessions when ponytail is installed.

> **Prerequisite:** This addon assumes ponytail is installed and active in this session. If
> `/ponytail` is not a recognized command, stop and install it first — see `ponytail-setup.md`.
> Without ponytail loaded, the precedence rules below govern nothing.

## Precedence Rules

Ponytail governs what gets built and how complex it is; PDCA governs how it is verified. Where
the two disagree, three narrow rules apply — everything else in ponytail (the ladder,
root-cause bug fixes, shortest-correct-diff, `# ponytail:` markers) applies unchanged:

1. **Ordering wins for PDCA.** Ponytail's verification-after-code yields to red-green-refactor.
   The CALLED SHOT still comes before any code.
2. **No trivial-code exemption.** Ponytail's "trivial one-liners need no test" does not apply —
   PDCA CHECK asserts no untested implementation was committed.
3. **Fixtures win for PDCA.** Ponytail's "no frameworks or fixtures required" yields to "add
   tests to existing fixtures rather than proliferate new test files."

---

## Mode → Phase Guidance

This is advice on which ponytail mode to pick per PDCA phase — not a mode-setting mechanism.
PDCA reads ponytail's mode; it never sets it. See `ponytail-setup.md` for how to set mode.

| Mode | Effect in PLAN | Effect in DO | When |
|---|---|---|---|
| `lite` | Names the lazier alternative; you pick | Flags simpler options before each step | Default when pairing with PDCA — adds the simplicity lens without pushing back on decisions already made in PLAN |
| `full` | Ladder enforced on scope | Shortest working diff, stdlib-first | Greenfield, or when you suspect over-engineering |
| `ultra` | Challenges whether steps should exist at all | Scope pushback during implementation | Over-engineered codebases. Avoid in DO — it relitigates PLAN decisions mid-implementation |

---

## Deliberate Simplifications

This addon is deliberately two files, not six like beads-addon. If a retrospective shows PLAN
needs its own ponytail guidance distinct from DO, the upgrade path is to split this file into
per-phase files mirroring beads-addon's structure — not to grow this file indefinitely.
