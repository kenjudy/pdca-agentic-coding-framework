# Building the PDCA Framework Skill

This document explains how to build and install the PDCA Framework skill package.

## Quick Start

**Just want to use the skill?** See [README.md](README.md) for installation instructions.

**Running unit tests** (no API key, runs in CI):
```bash
cd claude-skill
uv sync --extra test
bash run-tests.sh
```

**Running eval tests** (requires `ANTHROPIC_API_KEY` in `.env`, ~$2-5/run, on-demand only):
```bash
cd claude-skill
uv sync --extra eval
bash run-evals.sh
```

**Building from source:**

**macOS/Linux (Bash):**
```bash
# Build the skill package
./build-skill.sh

# Install for Claude Code
./install-skill.sh personal   # Available across all projects
# or
./install-skill.sh project    # Available in current project only
```

**Windows (PowerShell):**
```powershell
# Build the skill package
.\build-skill.ps1

# Install for Claude Code
.\install-skill.ps1 personal   # Available across all projects
# or
.\install-skill.ps1 project    # Available in current project only
```

## Overview

The skill package is automatically composed from your master prompt files located in the repository root:

```
Master Sources → Build Script → Skill Package → Installation
├── 1. Plan/1a...md       ─┐
├── 1. Plan/1b...md       ─┤→ src/references/plan-prompts.md  ─┐
├── 2. Do/2...md          ─┤→ src/references/do-prompts.md     │
├── 3. Check/3...md       ─┤→ src/references/check-prompts.md  ├→ pdca-framework.skill
├── 4. Act/4...md         ─┤→ src/references/act-prompts.md    │                         │
└── Human Working Agr...  ─┤→ src/references/working-agr...md  │                         │
                          └→ src/SKILL.md (manually maintained) ─┘                         │
                                                                                            │
For Claude.ai: Upload .skill file ←───────────────────────────────────────────────────────┘
For Claude Code: Extract to ~/.claude/skills/pdca-framework/ ←────────────────────────────┘
```

## Prerequisites

**macOS/Linux:**
- Bash shell (built-in)
- `zip` command (pre-installed)
- Master source files in their expected locations

**Windows:**
- PowerShell 5.1 or later (built-in on Windows 10+)
- Master source files in their expected locations

## Building the Skill

### Quick Build

From the repository root:

**macOS/Linux:**
```bash
cd claude-skill
./build-skill.sh
```

**Windows:**
```powershell
cd claude-skill
.\build-skill.ps1
```

### What the Build Script Does

1. **Verifies** all master source files exist
2. **Composes** reference files:
   - Combines `1a` and `1b` into `plan-prompts.md`
   - Copies other phase files to `references/`
3. **Creates** the skill package (ZIP with `.skill` extension)
4. **Reports** the package size and contents

### Build Output

```
claude-skill/
├── build-skill.sh              # The build script (macOS/Linux)
├── build-skill.ps1             # The build script (Windows)
├── install-skill.sh            # Installation script (macOS/Linux)
├── install-skill.ps1           # Installation script (Windows)
├── pdca-framework.skill       # Generated (can be committed or ignored)
└── src/                        # Generated source files
    ├── SKILL.md               # Manually maintained
    └── references/            # Auto-generated from masters
        ├── plan-prompts.md
        ├── do-prompts.md
        ├── check-prompts.md
        ├── act-prompts.md
        └── working-agreements.md
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

### Option 1: Commit Generated Files (Recommended)

**Pros:**
- Users can download the skill directly from GitHub
- See exactly what's in the latest release
- Easy to track changes in skill package

**Cons:**
- Generated files tracked in git

**Setup (macOS/Linux):**
```bash
# Build and commit
./build-skill.sh
git add src/references/ pdca-framework.skill
git commit -m "Rebuild skill from updated master prompts"
```

**Setup (Windows):**
```powershell
# Build and commit
.\build-skill.ps1
git add src/references/ pdca-framework.skill
git commit -m "Rebuild skill from updated master prompts"
```

### Option 2: Ignore Generated Files

**Pros:**
- Only source files in git
- Build from masters on demand

**Cons:**
- Users must build locally
- Can't download skill directly from GitHub

**Setup:**
Add to `.gitignore`:
```gitignore
# Build artifacts
claude-skill/src/references/
claude-skill/pdca-framework.skill
claude-skill/temp_package/
```

Then build locally (macOS/Linux):
```bash
./build-skill.sh
# Use the skill but don't commit it
```

Or build locally (Windows):
```powershell
.\build-skill.ps1
# Use the skill but don't commit it
```

## Customizing the Build

### Change Master File Locations

**For macOS/Linux:** Edit `build-skill.sh` and update these variables:

```bash
MASTER_1A="$REPO_ROOT/1. Plan/1a Analyze..."
MASTER_1B="$REPO_ROOT/1. Plan/1b Create..."
# etc.
```

**For Windows:** Edit `build-skill.ps1` and update these variables:

```powershell
$Master1A = Join-Path (Join-Path $RepoRoot "1. Plan") "1a Analyze..."
$Master1B = Join-Path (Join-Path $RepoRoot "1. Plan") "1b Create..."
# etc.
```

### Add Additional Files

To include more files in the skill package:

1. Add the source to `src/references/`
2. Update the packaging command:

**In `build-skill.sh`:**
```bash
zip -r "$SKILL_FILE" \
    SKILL.md \
    references/plan-prompts.md \
    references/your-new-file.md \  # Add here
    ...
```

**In `build-skill.ps1`:**
```powershell
Copy-Item $YourNewFile -Destination $tempReferencesDir -Force
```

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
   ls -lh src/references/
   cat src/references/plan-prompts.md  # Check composition
   ```

## Troubleshooting

### "Master file not found" error

**Cause:** Master files moved or renamed

**Solution:** Update the paths in `build-skill.sh` (macOS/Linux) or `build-skill.ps1` (Windows)

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

### "NotSupportedArchiveFileExtension" error (Windows)

**Cause:** Old version of the script trying to create .skill directly

**Solution:** Update to the latest `build-skill.ps1` which creates .zip first, then renames

### Path not found errors (Windows)

**Cause:** Spaces in paths not properly quoted

**Solution:** The script handles this automatically, but ensure you're using the latest version

### ZIP file seems wrong

**Cause:** Working directory issue in script

**Solution:** Ensure script runs from `claude-skill/` directory:

**macOS/Linux:**
```bash
cd claude-skill && ./build-skill.sh
```

**Windows:**
```powershell
cd claude-skill; .\build-skill.ps1
```

## Automation Ideas

### Git Hook (Pre-Commit)

Automatically rebuild when masters change:

```bash
# .git/hooks/pre-commit
#!/bin/bash
cd claude-skill && ./build-skill.sh
git add src/references/ pdca-framework.skill
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
      - run: cd claude-skill && ./build-skill.sh
      - uses: actions/upload-artifact@v2
        with:
          name: pdca-skill
          path: claude-skill/pdca-framework.skill
```

### Makefile (macOS/Linux)

Add to repository root:

```makefile
.PHONY: skill
skill:
	cd claude-skill && ./build-skill.sh

.PHONY: skill-clean
skill-clean:
	rm -f claude-skill/pdca-framework.skill
	rm -rf claude-skill/src/references/
```

Usage: `make skill`

### Build Script (Windows)

Create `build.bat` in repository root:

```batch
@echo off
cd claude-skill
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
`https://github.com/kenjudy/pdca-code-generation-process/releases`

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
python3 -m scripts.quick_validate "/path/to/claude-skill/pdca-framework"
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
