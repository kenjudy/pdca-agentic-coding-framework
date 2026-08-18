# Building the PDCA Framework Skill

This document explains how to build and install the PDCA Framework skill package.

## Quick Start

**Just want to use the skill?** See [README.md](README.md) for installation instructions.

**Running unit tests** (no API key, runs in CI):
```bash
cd skill
uv sync --extra test
bash run-tests.sh
```

**Running eval tests** (requires `ANTHROPIC_API_KEY` in `.env`, ~$2-5/run, on-demand only):
```bash
cd skill
uv sync --extra eval
bash run-evals.sh
```

**Building from source:**

**macOS/Linux (Bash):**
```bash
# Build the skill package
./build-skill.sh

# Install for Claude Code
./install-skill.sh claude     # Available across all projects
# or
./install-skill.sh project    # Available in current project only
# or install for Codex
./install-skill.sh codex      # Available across all projects
```

**Windows (PowerShell):**
```powershell
# Build the skill package
.\build-skill.ps1

# Install for Claude Code
.\install-skill.ps1 claude     # Available across all projects
# or
.\install-skill.ps1 project    # Available in current project only
# or install for Codex
.\install-skill.ps1 codex      # Available across all projects
```

## Overview

The skill package is automatically composed from your master prompt files located in the repository root. `build-skill.sh` (macOS/Linux) and `build-skill.ps1` (Windows) are thin wrappers — all of the actual composition logic lives in one place, `build.py` (see [Architecture](#architecture) below):

```
Master Sources → build.py → Skill Package → Installation
├── 1. Plan/1a...md       ─┐
├── 1. Plan/1b...md       ─┤→ pdca-framework/references/plan-prompts.md  ─┐
├── 2. Do/2...md          ─┤→ pdca-framework/references/do-prompts.md     │
├── 3. Check/3...md       ─┤→ pdca-framework/references/check-prompts.md  ├→ pdca-framework.skill
├── 4. Act/4...md         ─┤→ pdca-framework/references/act-prompts.md    │
└── Human Working Agr...  ─┤→ pdca-framework/references/working-agr...md  │
                          └────────────────────────────────────────────────┘
   (pdca-framework/SKILL.md is manually maintained, not generated, but
    ships in the same package)

For Claude.ai: Upload .skill file
For Claude Code: Extract to ~/.claude/skills/
For Codex: Extract to ~/.agents/skills/
```

### Architecture

`skill/build.py` is the single implementation of the build (issue #114). `build-skill.sh` and
`build-skill.ps1` are thin wrappers — they locate a Python interpreter and call `build.py`, and
carry no build logic of their own — so macOS/Linux and Windows cannot drift apart the way they
did before this extraction: there is only one place mistakes, or fixes, can happen.

#### The `build.py` interface

```python
def build(skill_dir: Path) -> Path:
    """Build the skill package. Returns the path to the written .skill zip."""
```

`skill_dir` is the `skill/` directory. Every other path derives from it:

```
skill_dir ─┬─ repo_root    = skill_dir/..                        masters: "1. Plan/", "2. Do/", …
           ├─ core_dir     = skill_dir/pdca-framework            SKILL.md, addon sources, references/ output
           │    ├─ beads-addon/ · ponytail-addon/
           │    └─ claude-addon/injections/
           └─ skill_file   = skill_dir/pdca-framework.skill      the zip
```

Neither wrapper passes `skill_dir` — `build.py`'s own `main()` derives it as
`Path(__file__).parent`, so the build always locates itself from where `build.py` lives rather
than from the caller's working directory or from anything a wrapper computes. The wrappers only
find an interpreter and hand it the path to `build.py`. `build` returns the zip path so
programmatic callers, which do pass `skill_dir` explicitly, need not reconstruct it.

#### Stale-artifact masking

`build.py` writes every generated file with `write_text()`, which **truncates an existing file in
place and leaves its mode untouched.** That is harmless for content — the new text always fully
replaces the old — but it is not harmless for permissions: a build that follows an earlier build
can inherit filesystem state the earlier build left behind. Concretely, if a prior run had set
`export-requirements.sh` to `0o755` on disk, a `build.py` run over that same tree would produce a
correctly-executable file *even if `build.py` never set `external_attr` on the zip member itself*
— the file on disk was already executable, `write_text()` didn't change that, and the resulting
package would look right by accident.

This actually happened during this extraction's Step 3: the first draft of the executable-bit test
passed against a tree still holding a leftover `0o755` from an earlier bash build — a real false
pass, not a hypothetical. It is why:

- **`EXECUTABLE_MODE` is a literal `0o755` in `build.py`**, not derived from the on-disk mode of
  `export-requirements.sh`. Deriving it from disk would silently reintroduce the same
  build-history dependency the bug exploited.
- **The PowerShell/bash parity test (`test_powershell_build_matches_bash` in
  `tests/test_builder.py`) calls `_clean_build_artifacts()` before *each* side of the
  comparison** — once before the bash build, once before the ps1 build — removing
  `pdca-framework/references/`, the stale `skill/src/` a pre-extraction `build-skill.ps1` used to
  leave behind, and the `.skill` file itself. Comparing two builds without forcing both to start
  from scratch risks the same false pass.

## Prerequisites

**macOS/Linux:**
- Bash shell (built-in)
- Python 3 (`build.py` is stdlib-only — no `uv`/venv needed to build, just to run the test suite)
- Master source files in their expected locations

**Windows:**
- PowerShell 5.1 or later (built-in on Windows 10+)
- A working Python 3 interpreter on `PATH` as `python3` or `python`
- Master source files in their expected locations

## Building the Skill

### Quick Build

From the repository root:

**macOS/Linux:**
```bash
cd skill
./build-skill.sh
```

**Windows:**
```powershell
cd skill
.\build-skill.ps1
```

### What the Build Script Does

Both `build-skill.sh` and `build-skill.ps1` do nothing but locate a Python interpreter and invoke
`build.py`, which then:

1. **Verifies** the required source files exist (`SKILL.md`, the addon injections directory)
2. **Composes** reference files into `pdca-framework/references/`:
   - Combines `1a` and `1b` into `plan-prompts.md`
   - Strips the license/attribution block from the phase prompt masters and working agreements
   - Applies `<!-- CLAUDE_INJECT: key -->` replacements to the four phase prompt files
   - Copies the beads/ponytail addon sources and `testing-anti-patterns.md` in verbatim (not
     license-stripped — see `COPIED_FROM_MASTER` / `COPIED_FROM_ADDON` in `build.py`)
3. **Creates** the skill package (a ZIP with a `.skill` extension, rooted at `pdca-framework/`)
4. **Reports** the package size and file count

### Build Output

```
skill/
├── build-skill.sh               # Thin wrapper (macOS/Linux): locates python3, calls build.py
├── build-skill.ps1              # Thin wrapper (Windows): locates python3/python, calls build.py
├── build.py                     # The build implementation — the only place build logic lives
├── install-skill.sh             # Installation script (macOS/Linux)
├── install-skill.ps1            # Installation script (Windows)
├── pdca-framework.skill         # Generated: the installable zip
└── pdca-framework/
    ├── SKILL.md                 # Manually maintained
    ├── beads-addon/sources/     # Manually maintained (optional beads integration)
    ├── ponytail-addon/sources/  # Manually maintained (optional ponytail integration)
    ├── claude-addon/injections/ # Manually maintained (CLAUDE_INJECT content)
    └── references/              # Generated by build.py — gitignored, never edit directly
        ├── plan-prompts.md
        ├── do-prompts.md
        ├── check-prompts.md
        ├── act-prompts.md
        ├── working-agreements.md
        ├── testing-anti-patterns.md
        ├── plan-beads-addon.md
        ├── do-beads-addon.md
        ├── check-beads-addon.md
        ├── act-beads-addon.md
        ├── beads-setup.md
        ├── beads-workflow.md
        ├── ponytail-setup.md
        ├── ponytail-workflow.md
        └── scripts/
            └── export-requirements.sh   # Packaged with the owner-execute bit set
```

## When to Rebuild

Rebuild the skill whenever you update any of these master files:

- `1. Plan/1a Analyze to determine approach for achieving the goal.md`
- `1. Plan/1b Create a detailed implementation plan.md`
- `2. Do/2. Test Drive the Change.md`
- `3. Check/3. Completeness Check.md`
- `4. Act/4. Retrospect for continuous improvement.md`
- `Human Working Agreements.md`

## Git Strategy

This repo does not commit generated files. `.gitignore` excludes `pdca-framework/references/`,
`pdca-framework.skill`, and `pdca-framework-beads.skill` — a `git status` after building locally
should show nothing to commit from the build itself.

Distribution happens through the release workflow instead: pushing a `v*.*.*` tag triggers
`.github/workflows/release.yml`, which runs the test suite, builds the package, and attaches
`pdca-framework.skill` to a GitHub Release as a downloadable artifact. That's what
[GitHub Releases](https://github.com/kenjudy/pdca-agentic-coding-framework/releases) links to —
not a checked-in copy of the build output.

**Why:** committing generated files means every master-prompt edit produces a second diff (the
regenerated `references/` and zip) that has to be reviewed alongside the real change, and it
invites the two from drifting if a contributor edits the artifact directly instead of rebuilding.
Keeping only source files in git and building on demand — locally for development, in CI for
release — keeps the repo to one source of truth per file.

**Local build (not committed):**
```bash
./build-skill.sh   # macOS/Linux
.\build-skill.ps1  # Windows
# Use the skill but don't commit pdca-framework/references/ or pdca-framework.skill
```

**If you're vendoring this framework into a repo without a release pipeline:** committing the
generated files is a reasonable alternative — it lets users download the skill straight from
your repo instead of from a Releases page. Build, then `git add pdca-framework/references/
pdca-framework.skill` and remove the build-artifact lines from `.gitignore`. That is not what
this repo does, so don't follow it here.

## Customizing the Build

### Change Master File Locations

There is one place to edit, not two: `build-skill.sh` and `build-skill.ps1` carry no master
paths of their own — they call straight into `build.py`. Edit the `MASTER_*` constants near the
top of `skill/build.py`:

```python
MASTER_1A = "1. Plan/1a Analyze to determine approach for achieving the goal.md"
MASTER_1B = "1. Plan/1b Create a detailed implementation plan.md"
MASTER_DO = "2. Do/2. Test Drive the Change.md"
MASTER_ANTI_PATTERNS = "2. Do/Testing Anti-Patterns.md"
MASTER_CHECK = "3. Check/3. Completeness Check.md"
MASTER_ACT = "4. Act/4. Retrospect for continuous improvement.md"
MASTER_WORKING_AGREEMENTS = "Human Working Agreements.md"
```

These are relative to `repo_root` (the directory above `skill/`). The change applies to both
platforms automatically since both wrappers invoke the same `build.py`.

### Add Additional Files

To include another file in the skill package, everything happens in `skill/build.py` and
`skill/tests/test_build.py` — nothing in either wrapper script needs to change:

1. **Add the file to one of `build.py`'s copy/strip dicts**, depending on how it should be
   produced:
   - `STRIPPED_FROM_MASTER` — copied from a repo-root master with the license/attribution block
     stripped (e.g. the phase prompts, working agreements)
   - `COPIED_FROM_MASTER` — copied from a repo-root master verbatim, no stripping
   - `COPIED_FROM_ADDON` — copied verbatim from a source under `pdca-framework/*-addon/sources/`
     (e.g. a new beads or ponytail file)

   Each entry maps the destination filename under `references/` to its source path.

2. **Add the destination path to `MANIFEST`** in `build.py` — this tuple is what actually gets
   zipped, in addition to driving which files the copy dicts above are expected to produce. A
   file present in a copy dict but missing from `MANIFEST` will not ship; a file listed in
   `MANIFEST` that no copy dict (or the plan-prompts/injection/export-script special cases)
   produces will fail the build with `BuildError`.

3. **Add the packaged path to `EXPECTED_FILES`** in `skill/tests/test_build.py`, so the test
   suite's manifest assertion — and `test_builder_produces_expected_manifest` in
   `tests/test_builder.py` — stay in sync with what the build actually produces.

4. Rebuild (`bash build-skill.sh`) and re-run the test suite.

### Customize the Package Structure

The `.skill` file is a ZIP archive. You can customize:

- Directory structure inside the ZIP
- Which files are included
- Compression settings

## Testing the Skill

After building:

1. **Verify the package contents:**
   ```bash
   unzip -l pdca-framework.skill
   ```

2. **Test in Claude:**
   - Upload `pdca-framework.skill` to Claude.ai
   - Or install in Claude Code (skills sync automatically)
   - Test with: `@pdca-framework Show me the analysis prompt`

3. **Review generated files:**
   ```bash
   ls -lh pdca-framework/references/
   cat pdca-framework/references/plan-prompts.md  # Check composition
   ```

## Troubleshooting

### "Master file not found" error

**Cause:** Master files moved or renamed

**Solution:** Update the `MASTER_*` constants in `skill/build.py` — see
[Change Master File Locations](#change-master-file-locations). There is only one place to edit.

### Build succeeds but skill doesn't work

**Cause:** `SKILL.md` may need updating

**Solution:** Check that `SKILL.md` references the correct file paths

### Permission denied when running script (macOS/Linux)

**Cause:** Script not executable

**Solution:**
```bash
chmod +x build-skill.sh
```

### Execution policy error (Windows)

**Cause:** PowerShell execution policy blocks scripts

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or run with bypass:
```powershell
powershell -ExecutionPolicy Bypass -File .\build-skill.ps1
```

### "No working Python interpreter found" (Windows)

**Cause:** `build-skill.ps1` probes `python3` then `python` on `PATH`, running each with
`--version` before trusting it — this rejects Microsoft Store stub executables that resolve via
`Get-Command` but aren't real interpreters. Neither candidate produced a working interpreter.

**Solution:** Install Python 3.11+ and ensure a real interpreter (not the Store stub) is on
`PATH`.

### ZIP file seems wrong

**Cause:** Working directory issue in script

**Solution:** Ensure script runs from `skill/` directory:

**macOS/Linux:**
```bash
cd skill && ./build-skill.sh
```

**Windows:**
```powershell
cd skill; .\build-skill.ps1
```

## Automation Ideas

### Git Hook (Pre-Commit)

Automatically rebuild when masters change:

```bash
# .git/hooks/pre-commit
#!/bin/bash
cd skill && ./build-skill.sh
git add pdca-framework/references/ pdca-framework.skill
```

### CI/CD (GitHub Actions)

Build and release on push:

```yaml
name: Build Skill
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: cd skill && ./build-skill.sh
      - uses: actions/upload-artifact@v2
        with:
          name: pdca-skill
          path: skill/pdca-framework.skill
```

### Makefile (macOS/Linux)

Add to repository root:

```makefile
.PHONY: skill
skill:
	cd skill && ./build-skill.sh

.PHONY: skill-clean
skill-clean:
	rm -f skill/pdca-framework.skill
	rm -rf skill/pdca-framework/references/
```

Usage: `make skill`

### Build Script (Windows)

Create `build.bat` in repository root:

```batch
@echo off
cd skill
powershell -ExecutionPolicy Bypass -File .\build-skill.ps1
cd ..
```

Usage: `build.bat`

## Releasing a New Version

Releases are automated via `.github/workflows/release.yml`. Pushing a semver tag
triggers the workflow: it runs tests, builds the skill, and publishes a GitHub Release
with `pdca-framework.skill` attached as a downloadable artifact.

**To cut a release:**

1. Update the version in `README.md` (search for `v1.0.0`)
2. Note the change in `CHANGELOG.md` (repo root)
3. (Optional) Run Anthropic's official skill validator — see [Pre-Release Validation](#pre-release-validation) below
4. Commit and push to main
5. Tag and push:

```bash
git tag v1.x.x
git push --tags
```

The Action runs automatically. The release appears at:
`https://github.com/kenjudy/pdca-agentic-coding-framework/releases`

The README's download link uses `/releases/latest/download/pdca-framework.skill` and
resolves to the newest release automatically — no link update needed.

## Pre-Release Validation

Anthropic provides a `quick_validate.py` script in their [`anthropics/skills`](https://github.com/anthropics/skills) repository that checks SKILL.md spec compliance: frontmatter schema, allowed keys, kebab-case name format, and description constraints. Our CI tests cover the same ground, but this is the authoritative source.

**One-time setup:**

```bash
git clone https://github.com/anthropics/skills /tmp/anthropics-skills
pip install pyyaml  # if not already installed
```

**Run before releasing:**

```bash
cd /tmp/anthropics-skills/skills/skill-creator
python3 -m scripts.quick_validate "/path/to/skill/pdca-framework"
# Expected output: Skill is valid!
```

This is a manual pre-release check, not wired into CI. Re-clone if `/tmp/anthropics-skills` has been cleared.

**What it validates:**
- `SKILL.md` frontmatter is valid YAML
- `name` is present, kebab-case, ≤64 chars
- `description` is present, no angle brackets, ≤1024 chars
- No unexpected frontmatter keys (allowed: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`)

Note: The spec allows descriptions up to 1024 chars. Our `test_description_under_200_chars` enforces a stricter 200-char limit as a UX discipline constraint for marketplace display.

## Contributing

When submitting PRs that modify master prompts:

1. Update the master files in their original locations
2. Run the build script to regenerate the skill:
   - macOS/Linux: `./build-skill.sh`
   - Windows: `.\build-skill.ps1`
3. Commit both the masters and the regenerated files
4. Note in PR: "Skill rebuilt from updated masters"

---

**Questions?** Open an issue on [GitHub](https://github.com/kenjudy/pdca-agentic-coding-framework)
