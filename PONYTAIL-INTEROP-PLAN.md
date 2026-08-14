# Implementation Plan: Optional Ponytail Interop

> **Working artifact.** This file exists so the plan survives across sessions and threads.
> Delete it before merging to `main`.
>
> **Branch:** `claude/pdca-ponytail-interop-r5u670` — all work lands here.
> **Produced by:** PDCA PLAN phase (1a analysis + 1b plan), Opus 5, 2026-08-14
>
> **Progress:** Step 0 complete (eval baseline recorded 2026-08-14). Step 1 complete
> (`7bf13af`, verified green: 134 passed, ruff clean). Next: Step 1b.

---

## Goal

After this session, the pdca-framework skill offers **optional** interoperation with
[ponytail](https://github.com/DietrichGebert/ponytail) through a progressive-disclosure addon,
so a human who has ponytail installed gets explicit rules for how its minimalism guidance
yields to PDCA's TDD discipline — and a human who does not have ponytail installed pays
nothing for the feature.

---

## Background for a fresh session

### What ponytail is

An AI-agent minimalism framework (MIT, © DietrichGebert). It installs as a plugin across 20+
agent platforms and instructs the agent to climb a decision ladder before writing code:

1. Does this need to exist? → no: skip it (YAGNI)
2. Already in this codebase? → reuse it
3. Stdlib does it? → use it
4. Native platform feature? → use it
5. Installed dependency? → use it
6. One line? → one line
7. Only then: the minimum that works

It owns its own mode state via `/ponytail lite|full|ultra|off`, `PONYTAIL_DEFAULT_MODE`, and
`~/.config/ponytail/config.json`. It ships slash commands including `/ponytail-review`
(flags over-engineering in the current diff) and `/ponytail-debt` (harvests deferred shortcuts
marked with `# ponytail:` comments).

### Ponytail's actual testing rule (verified against its AGENTS.md)

> "Lazy code without its check is unfinished." Non-trivial logic requires one runnable
> verification — a self-contained assert-based demo or minimal test file (no frameworks or
> fixtures required). Trivial one-liners need no test.

**Ponytail is not anti-test.** Any design that "suspends ponytail's testing guidance" wholesale
is both imprecise and unnecessary. The real conflicts are three narrow ones (see Step 9).

### The architectural precedent this plan follows

The repo already solves "optional third-party integration" twice:

| Pattern | Mechanism | Location |
|---|---|---|
| **beads-addon** | Separate source files → copied by `build-skill.sh` into `references/*-beads-addon.md`; surfaced via a short SKILL.md section plus per-phase `**Beads (Optional)**: See references/...` pointers. Never loaded unless the human opts in. | `skill/pdca-framework/beads-addon/sources/` |
| **claude-addon** | `<!-- CLAUDE_INJECT: key -->` HTML-comment markers inside the Obsidian masters, replaced at build time from `claude-addon/injections/<key>.md`. Invisible in Obsidian. | `skill/pdca-framework/claude-addon/injections/` |

Beads also uses a third, lighter form: an inline `**If beads is active**` guard clause in the
DO master (`2. Do/2. Test Drive the Change.md:72`). The established idiom for a cross-phase
session mode is therefore: **declare once in SKILL.md, re-state as a short guard clause per
phase, keep the bulk in a reference file.**

This plan uses that idiom. It does not introduce a fourth mechanism.

---

## Decisions already made (do not relitigate)

1. **Addon route, not an inline block in the PLAN prompt.** An inline block would load for every
   PDCA user whether or not they have ponytail, and would edit `1. Plan/1a...md` — forcing a
   re-run of both `TestPrompt1aEvals` and `TestPrompt1bEvals` (they share `plan-prompts.md`).
2. **Reference ponytail, don't vendor it.** If ponytail is installed, its ladder is already in
   the agent's context; restating it is duplication that drifts when upstream `AGENTS.md`
   changes. PDCA supplies only what ponytail cannot know: how its rules yield to TDD.
   MIT attribution goes in the setup file.
3. **Mode stays ponytail's.** PDCA reads `/ponytail lite|full|ultra|off`; it never sets or
   re-declares mode. Two sources of truth for mode can disagree.
4. **Two addon files, not beads' six.** Marked as a deliberate simplification; upgrade path is
   to split out per-phase files if a retrospective shows PLAN needs its own guidance.
5. **Explicit precondition block** at the top of both addon files (see Step 3). Without it, a
   human who activates the guard clause without ponytail installed gets precedence rules
   governing a ladder that is not in context.

---

## Verified file references

All line numbers verified against the working tree on 2026-08-14. Re-verify before editing —
they shift as soon as Step 1 lands.

| Reference | Content |
|---|---|
| `skill/tests/test_build.py:26` | `EXPECTED_FILES = [` |
| `skill/tests/test_build.py:150` | `def test_addon_references_are_optional(self):` (renamed by Step 1) |
| `skill/SUPERVISION-PROTOCOL.md:165` | phase → eval-class mapping row for `1. Plan/1a...md` |
| `2. Do/2. Test Drive the Change.md:72` | `**If beads is active** ...` — the guard-clause precedent |
| `3. Check/3. Completeness Check.md:26` | `- [ ] No TODO implementations remaining created by this test driving` |
| `3. Check/3. Completeness Check.md:47` | tool-check line probing `/simplify` and `/security-review` |
| `skill/pdca-framework/SKILL.md` | 126 lines (cap is 500 — ample room) |

---

## Preparatory refactoring

`test_beads_references_are_optional` (`skill/tests/test_build.py:140`) hardcodes `beads` in its
regex. Ponytail needs the identical guarantee. Copy-pasting a second near-identical test is
exactly the duplication ponytail's rung #2 forbids — so generalize first, as a `refactor:`
commit with all tests still green, before any ponytail file exists.

---

## Steps

Model tags are recommendations, not requirements. Each step is one commit. **Stop for human
review after each step** — do not batch.

| # | Type | Model | Step | Called shot / acceptance |
|---|---|---|---|---|
| 0 | prep | — | ✅ **DONE** — Baseline recorded 2026-08-14: `TestPrompt2Evals` 4/4 passed (scores 0.80/n/a/0.90/0.80 vs. 0.50 threshold); `TestPrompt3Evals` 3/3 passed (scores 0.67±0.35/0.90/0.90±0.0 vs. 0.50 threshold). Reports: `skill/eval/results/report_20260814_164716.md` (Prompt2), `report_20260814_164922.md` (Prompt3) — gitignored, local only | Numbers written down before any master edit |
| 1 | `refactor:` | Sonnet 5 | ✅ **DONE** (`7bf13af`) — Generalized `test_beads_references_are_optional` → `test_addon_references_are_optional` over `ADDON_SLUGS = ["beads"]`, and `test_beads_addon_source_files_exist` → `test_addon_source_files_exist`; added `ADDON_SOURCE_FILES` dict | Verified: 134 passed, 135 subtests, ruff clean; zero new files |
| 1b | `refactor:` | Sonnet 5 | **Decouple the two test drivers** (see "Sequencing correction" below): change `test_addon_source_files_exist` to iterate `ADDON_SOURCE_FILES.items()` instead of `ADDON_SLUGS` | All tests still green before and after; no behavior change while only `beads` exists |
| 2 | `test:` **RED** | Sonnet 5 | Add `"ponytail": PONYTAIL_SOURCE_FILES` to `ADDON_SOURCE_FILES` **only** — do NOT touch `ADDON_SLUGS` yet | Expected failure, **one test**: `test_addon_source_files_exist` — `Ponytail source file missing: .../ponytail-addon/sources/ponytail-setup.md` |
| 3 | `feat:` GREEN | Sonnet 5 | Create `skill/pdca-framework/ponytail-addon/sources/ponytail-setup.md` and `ponytail-workflow.md` (content spec below) | Step-2 test passes; nothing else changes |
| 4 | `test:` **RED** | Sonnet 5 | Add both files to `EXPECTED_FILES` (`test_build.py:26`) | Expected failure: `pdca-framework/references/ponytail-setup.md` not in zip namelist |
| 5 | `feat:` GREEN | Sonnet 5 | `build-skill.sh`: verify block, copy step, **and the `zip -r` manifest** | Step-4 test passes. **The manifest is the trap** — files absent from it vanish silently; Step 4's test is the only thing that catches it |
| 6 | `test:` **RED** | Sonnet 5 | Add `"ponytail"` to `ADDON_SLUGS` — this is the step that arms the optionality check | Expected failure, **one test**: `test_addon_references_are_optional` — `No ponytail references found in SKILL.md` (the `len > 0` assert). Verified by simulation on 2026-08-14 |
| 7 | `feat:` GREEN | Sonnet 5 | SKILL.md → "Ponytail Integration (Optional)" section, mirroring the beads section | Passes; SKILL.md stays under the 500-line cap |
| 8 | `feat:` **master** | Opus 5 | `3. Check/3. Completeness Check.md`: add `/ponytail-review` to the tool-check line at :47; add one line reconciling `# ponytail:` markers with the no-TODO assertion at :26 | Rebuild; re-run `TestPrompt3Evals`; all previously passing scenarios still pass |
| 9 | `feat:` **master** | Opus 5 | `2. Do/2. Test Drive the Change.md`: `**If ponytail is active**` guard clause + the three precedence rules | Rebuild; re-run `TestPrompt2Evals`; no regression vs. baseline |
| 10 | `docs:` | Opus 5 | `README.md`, `skill/README.md`, `CLAUDE.md`, `CHANGELOG.md` | Ponytail appears alongside beads as an optional integration |

Steps 8 and 9 are **separate commits with separate eval runs** — one discrete change per
CLAUDE.md's "Validating Prompt Changes."

### Sequencing correction (found after Step 1)

**This was a flaw in the original plan, not in the Step 1 work.** Step 1 faithfully implemented
what the plan specified; the plan specified something that breaks TDD discipline one step later.

As written, both `test_addon_source_files_exist` and `test_addon_references_are_optional` iterate
`ADDON_SLUGS`. So the original Step 2 — "add `ponytail` to `ADDON_SLUGS` **and** the source list" —
would drive **two** tests red at once, violating the framework's one-failing-test-at-a-time rule.
Confirmed by simulation: adding the slug alone trips `test_addon_references_are_optional`
immediately, because SKILL.md carries no ponytail reference until Step 7.

The fix is Step 1b: give each test its own driver.

- `test_addon_source_files_exist` iterates `ADDON_SOURCE_FILES.items()` → armed by **Step 2**
- `test_addon_references_are_optional` iterates `ADDON_SLUGS` → armed by **Step 6**

Step 1b is a pure `refactor:` commit — while `beads` is the only addon, both forms iterate the
same single entry, so all tests stay green across the change.

### Model-switch note

Switching models mid-thread invalidates the prompt cache entirely (caches are model-scoped, no
escape hatch), and the 20-block cache lookback means switching *back* after a long run is also a
cold read. If splitting work by model, prefer a **fresh thread per model** carrying this file,
rather than switching inside one thread. Steps 1–7 in one Sonnet thread; Steps 8–10 in one Opus
thread with this file plus the two master prompts.

---

## Content spec

### Precondition block — top of BOTH addon files

> **Prerequisite:** This addon assumes ponytail is installed and active in this session. If
> `/ponytail` is not a recognized command, stop and install it first — see `ponytail-setup.md`.
> Without ponytail loaded, the precedence rules below govern nothing.

### `ponytail-setup.md`

- What ponytail is, in two sentences.
- Install pointer: link to `github.com/DietrichGebert/ponytail` — **do not vendor install
  instructions**, they drift.
- MIT attribution (© DietrichGebert).
- A one-line liveness check the agent can actually run to confirm ponytail is loaded.
- How mode is set (`/ponytail lite|full|ultra|off`) — stated as ponytail's, not PDCA's.

### `ponytail-workflow.md`

- Precondition block (above).
- **The three precedence rules** (Step 9 also carries these, condensed, in the DO master):

  1. **Ordering wins for PDCA.** Ponytail's verification-after-code yields to
     red-green-refactor. The CALLED SHOT still comes before any code.
  2. **No trivial-code exemption.** Ponytail's "trivial one-liners need no test" does not
     apply — PDCA CHECK asserts no untested implementation was committed.
  3. **Fixtures win for PDCA.** Ponytail's "no frameworks or fixtures required" yields to
     "add tests to existing fixtures rather than proliferate new test files."

  Everything else in ponytail — the ladder, root-cause bug fixes, shortest-correct-diff,
  `# ponytail:` markers — applies unchanged. **Ponytail governs what gets built and how complex
  it is; PDCA governs how it is verified.**

- **Mode → phase guidance** (advice on which ponytail mode to pick, *not* a mode-setting
  mechanism):

  | Mode | Effect in PLAN | Effect in DO | When |
  |---|---|---|---|
  | `lite` | Names the lazier alternative; you pick | Flags simpler options before each step | Default when pairing with PDCA — adds the simplicity lens without pushing back on decisions already made in PLAN |
  | `full` | Ladder enforced on scope | Shortest working diff, stdlib-first | Greenfield, or when you suspect over-engineering |
  | `ultra` | Challenges whether steps should exist at all | Scope pushback during implementation | Over-engineered codebases. Avoid in DO — it relitigates PLAN decisions mid-implementation |

- **Deliberate simplifications** marked as such, with upgrade paths (see Decisions #4).

### Step 8 — CHECK reconciliation line

`# ponytail:` markers are deliberate deferred shortcuts by definition (ponytail ships
`/ponytail-debt` to harvest them). CHECK's existing assertion at :26 says "No TODO
implementations remaining created by this test driving." A ponytail marker is exactly that,
spelled differently — so CHECK currently either flags it as a violation or, worse, silently
misses it. Add one line making the intended treatment explicit. This gap must close in the same
change that introduces the markers.

---

## Risks

| Risk | Mitigation |
|---|---|
| Eval regression on phases 2/3 | Steps 8 and 9 are independent commits; revert either alone |
| Zip manifest omission in `build-skill.sh` | Step 4's RED test exists specifically to catch it |
| Upstream ponytail `AGENTS.md` drifts | We reference rather than vendor; only the three precedence rules could go stale, and they describe PDCA's side |
| Line numbers in this file go stale | They shift as soon as Step 1 lands — re-verify before each edit |

**Rollback:** every step is its own commit. Steps 1–7 are additive and inert for non-ponytail
users; Steps 8–9 are the only master-prompt changes.

---

## Known issue — explicitly out of scope

**`skill/build-skill.ps1` is already out of sync with `build-skill.sh`.** The PowerShell script
copies only the 6 base reference files: no beads addon files, no `CLAUDE_INJECT` processing, no
license stripping (it uses plain `Copy-Item`). It produces a different, smaller skill package
than the shell script.

This is **pre-existing** and not caused by this work. Bringing it to parity means porting
injections, license stripping, and the beads addon — a separate substantial change. This plan
therefore touches only `build-skill.sh`, which leaves the two scripts one file further apart.

**Action:** file as a follow-up issue during ACT. Do not fix it inside this cycle — that is
scope expansion.

Also unassessed: `skill/install-skill.sh` carries beads-specific user-facing text at lines 36
and 131–145. Whether ponytail warrants equivalent install messaging is a judgment call for
Step 10; it is not required for the feature to work.

---

## Definition of Done

- [ ] `cd skill && bash run-tests.sh` green (ruff + pytest)
- [ ] `TestPrompt2Evals` and `TestPrompt3Evals` at or above the Step-0 baseline
- [ ] A non-ponytail user's built `plan-prompts.md` is byte-for-byte unchanged
- [ ] Docs updated (README, skill/README, CLAUDE.md, CHANGELOG)
- [ ] Pushed to `claude/pdca-ponytail-interop-r5u670`
- [ ] Human has signed off on CHECK and ACT

## CHECK step

Verify against this plan's acceptance criteria. Confirm no master edit regressed evals. Confirm
the non-ponytail user's context is unchanged. Confirm the `# ponytail:` marker reconciliation
actually landed in the CHECK master.

## ACT step

Retrospective (5–10 min). Specifically:

- Did "reference, don't vendor" hold up, or did we end up wanting the ladder inline after all?
- Was two addon files the right call, or does PLAN want its own?
- File the `build-skill.ps1` drift as a follow-up issue.
- `bd` is not installed in the environment where this plan was written and there is no
  `.beads/` directory — if beads is available in the executing session, file the follow-ups
  there; otherwise record them in `CHANGELOG.md` or as a GitHub issue.

## Session completion (from CLAUDE.md — mandatory)

1. File issues for remaining work
2. `cd skill && bash run-tests.sh`
3. Close finished issues, update in-progress ones
4. `git pull --rebase` → `bd sync` (if beads available) → `git push` → `git status` must show
   up to date with origin
5. Hand off with context for the next session

**Never** say "ready to push when you are" — push yourself.
