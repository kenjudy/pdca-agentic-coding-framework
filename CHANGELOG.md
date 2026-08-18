# PDCA Framework Skill - Update Summary

## Unreleased

### Build system — shared `build.py` extraction (#114)

- **Fixed silent drift between the two build scripts.** `build-skill.ps1` still targeted
  `skill/src`, a directory renamed to `skill/pdca-framework` long ago: it shipped 7 of 16 files at
  the wrong ZIP root, with raw `CLAUDE_INJECT` markers unreplaced and license/attribution blocks
  unstripped in 5 files, and it created an untracked `skill/src/` on every Windows build. Nothing
  caught it because nothing ever ran it — there was no test that executed `build-skill.ps1`.
- **Extracted the build into `skill/build.py`**, a single stdlib-only implementation. Both
  `build-skill.sh` and `build-skill.ps1` are now thin wrappers that locate a Python interpreter
  and call `build(skill_dir) -> Path`; neither carries composition, license-stripping, injection,
  or packaging logic of its own, so the two platforms can no longer diverge — there is only one
  place a fix or a mistake can happen.
- **Added `tests/test_builder.py::test_powershell_build_matches_bash`**, a parity test that runs
  both `build-skill.sh` and `build-skill.ps1` from a clean tree and asserts the resulting packages
  have identical member names and per-member SHA-256 hashes. Both builds now force a from-scratch
  state before comparison — `build.py` writes generated files via `write_text()`, which truncates
  an existing file in place but leaves its mode untouched, so a build that reuses a tree left over
  from an earlier build can inherit that build's file permissions and mask a defect in the current
  one. This is not hypothetical: the packaged-executable-bit test (`test_export_script_is_executable`)
  passed on its first draft for exactly this reason, before `build.py` actually set the permission
  bit itself. `BUILD.md` documents this as "Stale-artifact masking."
- **CI now hard-fails rather than skips the parity test when `pwsh` is missing.** A silently
  skipped parity test is indistinguishable from a passing one in pytest's summary line — exactly
  the blind spot that let the original drift go undetected — so under `CI=true` a missing `pwsh`
  is treated as a test failure, not a skip. Locally, without `CI=true`, the test still skips
  gracefully for contributors without PowerShell installed.
- `mypy` coverage widened from `eval tests` to `eval tests build.py` so the new module is
  type-checked in CI.

### Eval harness — mechanical matching repair

- **Fixed a defect that made the anti-rubber-stamp guard inoperable.** `check_mechanical` compared
  signal phrases against raw markdown, so `must_not_contain: "Status: Complete"` could never match
  the CHECK template's own `**Status:** Complete` rendering. A model certifying unfinished work in
  the format the template teaches was scored as passing — in the two scenarios written to catch
  exactly that. Emphasis is now stripped symmetrically before matching.
- Same defect in the other direction: colon-terminated phrases such as `Status:` and
  `Why this test first:` failed against `**Status**:` styling — 19 of the suite's 51 signal
  phrases were exposed. Underscores are deliberately preserved so code identifiers like
  `def deliver_webhook` are unaffected.
- **Eval reports now record every retry shot's output.** Previously only the first shot was kept,
  which discarded exactly the outputs needed to diagnose a mechanical failure.
- **`3-all-complete` scenario input rewritten** to supply evidence for all three checklist
  sections. It previously asked the model to audit TDD discipline, coverage, and structural
  findings while providing evidence for none, so declining to certify was the correct answer and
  the scenario scored it as a failure.

### New tooling

- **`skill/run-ab-eval.sh`** — interleaved A/B for master-prompt changes. Alternates arms within
  each pair so API-side drift affects both equally, and aborts rather than scoring a run that
  failed to execute.
- **`skill/eval/abstats.py`** — two-tailed Fisher exact test, pure stdlib, verified against
  published reference values. Added because an eyeballed p-value in the preceding cycle was wrong
  by a factor of two.
- `SUPERVISION-PROTOCOL.md` gains a section on attributing eval failures: never from a single run,
  never from sequential batches, and treat a suspiciously clean result as a harness bug until
  proven otherwise.

### Optional ponytail interop

- The pdca-framework skill now offers optional interoperation with
  [ponytail](https://github.com/DietrichGebert/ponytail) (MIT, © DietrichGebert), an AI-agent
  minimalism framework. Mirrors the existing beads-addon pattern: `references/ponytail-setup.md`
  and `references/ponytail-workflow.md`, surfaced via a "Ponytail Integration (Optional)" section
  in `SKILL.md`. Never loaded unless ponytail is already active in the session.
- Three precedence rules resolve the only real conflicts between ponytail's guidance and PDCA's
  TDD discipline — ordering (red-green-refactor still comes first), no trivial-code exemption, and
  existing-fixture preference over standalone assert demos. PDCA governs how work is verified;
  ponytail governs what gets built and how complex it is.
- `2. Do/2. Test Drive the Change.md` gains a one-line guard clause pointing to the addon.
  Deliberately not the full three rules inline — measurement during this cycle showed the DO
  master already enforces all three (a scenario invoking ponytail's trivial-one-liner exemption
  scored 1.00 against the *unmodified* prompt), so restating them would only triplicate them
  across the prompt, the addon, and `SKILL.md`.
- `3. Check/3. Completeness Check.md` gains one line reconciling `# ponytail:` deferred-shortcut
  markers with the existing "no TODO implementations remaining" assertion.
- Users without ponytail installed pay a small, measured cost: four lines totalling ~580 bytes,
  confined to two built prompt files (`check-prompts.md` +264 bytes, `do-prompts.md` +317 bytes),
  where the guard clauses read as inapplicable. `plan-prompts.md`, `act-prompts.md`,
  `working-agreements.md`, `testing-anti-patterns.md` and all six beads references are
  byte-for-byte unchanged. The two ponytail addon files ship in the package but are never loaded
  unless requested.

## v1.2.0 (2026-07-17)

### New Skills
- **update-changelog**: New skill that drafts changelog entries from commits ahead of `main`, groups them by category, shows a preview, and writes to `CHANGELOG.md` (or a named changelog file) only after user confirmation.

### Repository Split
- **human-directed-ai-workflow-builder** moved to its own repository: [kenjudy/human-directed-ai-workflow-builder](https://github.com/kenjudy/human-directed-ai-workflow-builder). Removed `5. Scaffold/`, `claude-skill/pdca-scaffold/`, `claude-skill/build-scaffold.sh`, `plugins/pdca-scaffold/`, `scaffolded-skills/`, and `presentations/` from this repo.

### Documentation
- Add `CONTRIBUTING.md`: contribution workflow, issue filing guidance,
  PDCA process, commit style, master prompt validation steps, and PR
  checklist including changelog format and version bump guidance
- **DO phase**: Added a fifth mandatory "Stub check" called-shot item to
  `2. Do/2. Test Drive the Change.md` — requires identifying whether a
  no-op stub could satisfy the test, and naming the next test a stub
  cannot satisfy.
- Renamed `skill/Agent.md` to `skill/SUPERVISION-PROTOCOL.md` for clarity;
  updated all `CLAUDE.md` references.
- Reordered `skill/README.md` so Installation precedes Building from
  Source, since most users should download the pre-built `.skill` from
  GitHub Releases rather than build it themselves. Release links now
  point to `/releases/latest` instead of a pinned version. Manual unzip
  (no repo clone needed) is now the primary recommended path for Claude
  Code and Codex, with matching PowerShell commands alongside every bash
  command; `install-skill.sh`/`.ps1` is presented as a repo-clone-only
  alternative.

### Repository Changes
- Renamed `claude-skill/` to `skill/` and added Codex installation support.
  Install locations now differ by tool:
  ```bash
  unzip -o pdca-framework.skill -d ~/.claude/skills/  # Claude Code
  unzip -o pdca-framework.skill -d ~/.agents/skills/  # Codex
  ```
- Fixed PowerShell skill descriptor path in `build-skill.ps1`.
- `install-skill.ps1` now prompts for install scope (user vs. machine)
  instead of assuming one.
- GitHub repository renamed from `kenjudy/pdca-framework` to
  `kenjudy/pdca-agentic-coding-framework`; all doc/URL references updated.

### Licensing
- Replaced CC0 with a dual license: CC BY 4.0 for documentation/prompts,
  MIT for source code in `skill/`.

### Build and Distribution
- Added `.claude-plugin/plugin.json` manifest so `pdca-framework` can be
  referenced via git-subdir source in the Stride plugin marketplace.

### Dependency Updates
- anthropic >=0.116.0
- deepeval >=4.1.0
- ruff >=0.15.21
- mypy >=2.3.0
- pytest >=9.1.1
- `actions/checkout` bumped from v6 to v7

### Migration Notes
- If your remote points to `kenjudy/pdca-framework`, update it to
  `kenjudy/pdca-agentic-coding-framework`.
- Documentation/prompts are now CC BY 4.0 (previously CC0); source code
  in `skill/` is now MIT licensed — review terms if you redistribute.
- References to `skill/Agent.md` should be updated to
  `skill/SUPERVISION-PROTOCOL.md`.
- Codex users: install to `~/.agents/skills/`, not `~/.claude/skills/`
  (see Repository Changes above).

---

## v1.1.0 (2026-05-28)

### New Skills
- **pdca-scaffold**: New first-class skill using 5-layer Socratic discovery to generate a domain-specific PDCA skill for any complex repeatable human task. Includes an active learning loop: after each ACT phase, proposes specific diffs back to the skill's own reference files; the human approves and commits; the skill sharpens over cycles without growing longer (anti-drift rule: +/- 10 net lines per refinement). Added `5. Scaffold/` master source files, `build-scaffold.sh`, and `pdca-scaffold/SKILL.md`.
- **daily-retro-pdca**: Scaffolded skill for structured daily and weekly retrospection. Added to `scaffolded-skills/`.

### PDCA Framework Redesigns
- **Socratic ACT phase**: ACT retrospective replaced with a five-stage Socratic structure. Agent analyzes the session transcript and presents data; human draws own insights and decides one thing to change. `rubric_4.py` rewritten to evaluate Socratic facilitation rather than directive Start/Stop/Keep output.
- **Claude Code injection system**: Marker-based injection added to `build-skill.sh` so Claude Code-specific content (plan mode, think/ultrathink prompts, slash commands) is embedded into built reference files at build time without polluting general-purpose Obsidian source files. Six injection files under `claude-addon/injections/`: goal-probe, plan-mode-probe, think-probe, do-think-probe, check-review-probe, act-retro-probes. `TestClaudeInjections` class (7 tests) added to `test_build.py`.
- **Unconditional CHECK and ACT steps**: CHECK and ACT are now required items in every plan, not conditional. Beads addon gains an explicit "Create CHECK and ACT Tasks" section.
- **Vacuous greens prevention**: Stub discipline and conditional-first test selection guidance added to DO phase to prevent Anti-Pattern #7 (ordering-triggered vacuous greens). `rubric_2.py` gains criterion #6 (stub discipline). `testing-anti-patterns.md` expanded with ordering-triggered sub-case.
- **Slash command prompts**: Slash command guidance added to plan phase prompts.

### Beads and Workflow
- `beads-setup.md`: Pre-flight check section verifies `bd --version`, `dolt version`, and `brew outdated beads dolt` before installation, with explicit upgrade commands.
- `beads-setup.md`: MCP server status check before install instructions.
- `beads-setup.md`: "Initializing Beads in a Project" section with "Post-Init: Align CLAUDE.md with Working Agreements" subsection.
- `beads-workflow.md`: "Resume a Session" section with orientation commands (`bd ready`, `bd list --status in_progress`, `bd show`) as the first thing to read when returning to in-progress work.
- `beads-workflow.md`: "Export Requirements Document" section with `export-requirements.sh` usage and a copyable slash command template.
- `beads-addon/scripts/export-requirements.sh`: New script to generate a structured requirements document from all open epics and their tasks.
- Git push is now human-initiated per working agreements; agent only commits.
- gitignore: git-native JSONL vs Dolt-native `bd dolt push` both documented as valid strategies.

### Build and Distribution
- **Removed `.beads/` from skill distribution**: Eliminates 375 lines of machine-specific runtime data (config, hooks, metadata, interactions, issues JSONL) from the built artifact.
- **Renamed `src/` to `pdca-framework/`**: Flattened `core/` directory for cleaner layout.
- **Release workflow**: `build-scaffold.sh` step added; `pdca-scaffold.skill` now attached to GitHub Releases alongside `pdca-framework.skill`.
- Research citations and acknowledgements added to README.

### Dependency Updates
- anthropic >=0.98.1
- deepeval >=3.9.9
- ruff >=0.15.12
- mypy >=1.20.2
- pytest >=9.0.3
- setuptools >=82.0.1
- python-dotenv >=1.2.2

---

## v1.0.2 (2026-03-27)

### Added
- `testing-anti-patterns.md` reference file in DO phase — adapted from obra/superpowers (MIT) with PDCA-specific additions covering six common TDD anti-patterns
- SKILL.md now links to the anti-patterns reference from the DO phase description
- CLAUDE.md at repo root incorporating session startup, beads workflow, and supervision rules from AGENTS.md for Claude Code auto-loading
- `.gitignore` suppresses iCloud sync conflict duplicates (`* 2.*`)

### Fixed
- `rubric_1b.py` clarified that ASCII structural diagrams are not "runnable code" violations
- Build pipeline (bash + PS1) and test_build.py updated for new anti-patterns file
- Enhanced GitHub Actions metrics workflows with percentile stats and commit quality scoring

## What Changed

Your PDCA skill has been updated with your latest prompts and working agreements from your GitHub repository.

### Major Updates

#### 1. **PLAN Phase - Analysis (1a)**
**New additions:**
- **Mandatory Architecture Pattern Discovery** - Three required codebase searches BEFORE any analysis
- **External System Validation** - Mandatory validation of external APIs/formats before implementation
- **Delegation Complexity Assessment** - Structured evaluation of task complexity
- **STOP CONDITIONS** - Blocking checkpoints to ensure proper pattern discovery

**Impact:** This prevents architectural drift and ensures AI agents discover and follow existing patterns before proposing solutions.

#### 2. **PLAN Phase - Detailed Planning (1b)**
**New additions:**
- **Execution Context** - Explicit guidance about TDD discipline and human supervision
- **Compilation ≠ Red Phase** - Clarification that compilation errors are not valid TDD red phase
- **Model Match Verification** - Checkpoint to ensure appropriate model complexity for task

**Impact:** Better alignment of agent behavior with TDD principles and more appropriate model selection.

#### 3. **DO Phase - TDD Implementation (2)**
**New additions:**
- **Integration Testing Emphasis** - Default to real components over mocks
- **Production Bug Handling** - Specific guidance for when unit tests can't replicate production bugs
- **Test Fixture Guidance** - Prefer adding to existing fixtures vs. creating new files
- **Real-World Validation** - Mandatory inspection of external system behavior before implementation

**Key principle changes:**
- ❌ DON'T test interfaces - test concrete implementations
- ❌ DON'T use compilation errors as RED phase
- ✅ DO create stub implementations that compile but fail behaviorally
- ✅ DO use real components over mocks when possible

**Impact:** Stronger emphasis on integration testing and real-world validation, reducing mock-heavy testing that misses production issues.

#### 4. **Working Agreements**
**Changes:**
- "STRICT TDD FOR ALL CHANGES" → "USE TDD FOR CHANGES" (slightly softer language)
- Removed redundant "Session Startup Protocol" section
- Maintained all 10 implementation guidelines unchanged

**Impact:** More pragmatic language while maintaining process discipline.

#### 5. **License & Attribution**
**Added to all files:**
- Creative Commons Attribution 4.0 International (CC BY 4.0)
- Attribution to Ken Judy with Claude Anthropic 4
- Link to GitHub repository
- Living document philosophy

### What Stayed the Same

- CHECK phase prompts (completeness verification)
- ACT phase prompts (retrospection structure)
- Overall PDCA cycle structure
- Human commitments for each phase
- Context drift recovery guidance

## Key Philosophy Shifts

### 1. Architecture-First Approach
The new analysis phase **requires** discovering existing patterns before proposing solutions. This prevents AI agents from inventing new abstractions when existing ones would suffice.

### 2. Integration Over Isolation
Strong preference for integration tests with real components over unit tests with mocks. Recognizes that many production bugs occur at integration boundaries.

### 3. Real-World Validation
Mandatory validation of external system behavior before implementation. No assumptions about data formats without seeing real examples.

### 4. Compilation vs. Behavior
Clear distinction that compilation is not TDD red phase - behavioral failures are. This prevents false reds from symbol resolution issues.

## How These Changes Help

**Reduces Technical Debt:**
- Mandatory pattern discovery prevents proliferation of new abstractions
- Real-world validation prevents assumptions that lead to bugs
- Integration testing catches issues unit tests miss

**Improves Code Quality:**
- Following existing patterns maintains consistency
- Testing real components reduces mock-heavy test suites
- Production bug handling ensures proper test coverage

**Better Human-AI Collaboration:**
- STOP conditions force critical thinking checkpoints
- Delegation complexity assessment helps right-size AI involvement
- Clear red/green definitions prevent confusion

## Files Updated

1. `references/plan-prompts.md` - Analysis and planning templates
2. `references/do-prompts.md` - TDD implementation guidance
3. `references/working-agreements.md` - Human commitments
4. `SKILL.md` - Added license and attribution

## Using the Updated Skill

The updated skill file `pdca-framework.skill` is in your outputs directory. Simply:

1. Remove the old version from Claude (if installed)
2. Upload the new version
3. All your conversations will now use the updated prompts

The skill will automatically load the new templates when triggered, so no changes to your workflow are needed.

---

**Generated:** 2025
**Version:** Based on GitHub repository prompts as of upload date
