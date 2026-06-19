# PDCA Framework

A Claude skill for human-supervised AI-assisted software development using Plan-Do-Check-Act methodology. Enforces explicit human-AI role separation, mandatory STOP gates, and TDD discipline.

> **Looking to build a custom AI workflow for any domain?** See [human-directed-ai-workflow-builder](https://github.com/kenjudy/human-directed-ai-workflow-builder) — generates a tailored PDCA skill for any complex repeatable task, with a built-in learning loop that sharpens it each cycle.

---

## pdca-framework — Three Ways to Use This Framework

### Option 1: Claude Skill - Standard (Recommended for Most Users)
**Install once, auto-triggers when coding**

- **Best for:** Consistent PDCA workflow across all coding sessions
- **Setup:** One-click installation in Claude.ai or Claude Code
- **Experience:** Automatic prompt loading, progressive disclosure
- **Token efficiency:** Loads only what's needed in background
- **Maintenance:** Update once, improves everywhere
- **Platforms:** macOS, Linux, Windows

📦 **[Get started with Standard Skill →](claude-skill/README.md)**

### Option 2: Claude Skill - with Beads (For Long-Running Work)
**Standard skill + persistent task tracking across sessions**

- **Best for:** Complex features spanning multiple days/weeks
- **Additional features:** Git-backed memory, cross-session continuity, searchable retrospectives
- **Requirements:** Install beads CLI and MCP server (Go 1.23+, ICU headers)
- **Works like:** Standard skill with optional beads commands in each phase
- **Backward compatible:** All beads commands are optional, skip them if beads not installed

🎯 **[Get started with Beads Skill →](claude-skill/README.md#beads-integration)**

### Option 3: Manual Prompts (Best for Customization)
**Copy/paste prompts as needed for each session**

- **Best for:** Customizing prompts for specific contexts
- **Setup:** Create symlinks or copy files to `.claude/` directory
- **Experience:** 100% visible in conversation, full control
- **Flexibility:** Easy to customize per-session
- **Portability:** Works with any AI tool, not just Claude
- **Platforms:** macOS, Linux, Windows

📝 **[Get started with Manual Prompts →](#manual-prompt-setup-claude-code)**

---

## Which Option Should I Choose?

| Use Case | Recommended Approach |
|----------|---------------------|
| Learning the framework | Start with **Manual Prompts** to understand each phase |
| Quick bug fix (single session) | **Standard Skill** for convenience |
| Regular coding sessions | **Standard Skill** for consistent workflow |
| Multi-day features | **Beads Skill** for cross-session continuity |
| Complex epics with dependencies | **Beads Skill** for task graph tracking |
| Team standardization | **Standard Skill** ensures consistency |
| Want searchable retrospectives | **Beads Skill** for git-backed learnings |
| Custom workflows | **Manual Prompts** for full flexibility |
| Non-Claude AI tools | **Manual Prompts** (skill is Claude-specific) |

**You can mix and match!** Many users:
- Install Standard Skill for daily work
- Keep Manual Prompts for special cases
- Add Beads Skill when starting complex, long-running features

---

## Why This Framework

Research shows AI code generation without human oversight leads to measurable quality degradation:
- 10x increase in duplicated code (GitClear 2024)
- 7.2% decrease in delivery stability per 25% AI adoption increase (Google DORA 2024)
- 19% slower development with AI tools vs. without (METR 2025)

PDCA Framework keeps humans actively engaged, empowered, and accountable while using structured prompts to regulate agent behavior toward transparency and discipline.

Read the full framework paper: [SOSA 2025 Notes](https://github.com/kenjudy/pdca-framework/blob/main/presentations/SOSA%202025/SOSA%202025%20Notes.md) — Presentation prepared for [XP 2026](https://kenjudy.us/presentations/human-centric-ai-code-generation/)

---

## PDCA Framework Overview

The PDCA workflow consists of four phases:
1. **Plan** - Analysis and detailed planning
2. **Do** - Test-driven implementation
3. **Check** - Completeness verification
4. **Act** - Retrospection and continuous improvement

---

# Manual Prompt Setup (Claude Code)

The rest of this document describes how to set up the manual prompt workflow in Claude Code using symlinked files.

For the Claude Skill setup (recommended), see **[claude-skill/README.md](claude-skill/README.md)** instead.

## Prerequisites

- Claude Code CLI installed
- Git

**Windows only:** Windows 10/11 with Developer Mode enabled (for symlinks without admin rights)

## Project Structure

After setup, your project should have:

```
your-project/
├── .claude/
│   ├── instructions.md          # Main workflow instructions
│   ├── prompts/                 # Symlinked phase templates
│   │   ├── 1a Analyze to determine approach for achieving the goal.md
│   │   ├── 1b Create a detailed implementation plan.md
│   │   ├── 2. Test Drive the Change.md
│   │   ├── 3. Completeness Check.md
│   │   └── 4. Retrospect for continuous improvement.md
│   └── validation.md            # Pre-commit checklist
├── .claudeignore                # Files for Claude to ignore
└── LinkPrompts.ps1              # Windows only: script to create symlinks
```

## Setup Steps

### 1. Configure Git for Symlinks

```bash
git config core.symlinks true
```

**Windows only:** Enable Developer Mode first:
1. Open Settings → Update & Security → For Developers
2. Turn on **Developer Mode**
3. Restart PowerShell/Terminal

### 2. Create Directory Structure

**macOS/Linux:**
```bash
mkdir -p .claude/prompts
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Path ".claude\prompts" -Force
```

### 3. Create Symlinks to Prompt Templates

**macOS/Linux:**
```bash
# Replace $TEMPLATES_PATH with your actual path to the PDCA templates
TEMPLATES_PATH="/path/to/pdca-templates"

ln -s "$TEMPLATES_PATH/1. Plan/1a Analyze to determine approach for achieving the goal.md" \
  ".claude/prompts/1a Analyze to determine approach for achieving the goal.md"
ln -s "$TEMPLATES_PATH/1. Plan/1b Create a detailed implementation plan.md" \
  ".claude/prompts/1b Create a detailed implementation plan.md"
ln -s "$TEMPLATES_PATH/2. Do/2. Test Drive the Change.md" \
  ".claude/prompts/2. Test Drive the Change.md"
ln -s "$TEMPLATES_PATH/3. Check/3. Completeness Check.md" \
  ".claude/prompts/3. Completeness Check.md"
ln -s "$TEMPLATES_PATH/4. Act/4. Retrospect for continuous improvement.md" \
  ".claude/prompts/4. Retrospect for continuous improvement.md"
```

**Windows (PowerShell):**
```powershell
$TEMPLATES_PATH = "C:\path\to\pdca-templates"

New-Item -ItemType SymbolicLink -Path ".claude\prompts\1a Analyze to determine approach for achieving the goal.md" -Target "$TEMPLATES_PATH\1. Plan\1a Analyze to determine approach for achieving the goal.md"
New-Item -ItemType SymbolicLink -Path ".claude\prompts\1b Create a detailed implementation plan.md" -Target "$TEMPLATES_PATH\1. Plan\1b Create a detailed implementation plan.md"
New-Item -ItemType SymbolicLink -Path ".claude\prompts\2. Test Drive the Change.md" -Target "$TEMPLATES_PATH\2. Do\2. Test Drive the Change.md"
New-Item -ItemType SymbolicLink -Path ".claude\prompts\3. Completeness Check.md" -Target "$TEMPLATES_PATH\3. Check\3. Completeness Check.md"
New-Item -ItemType SymbolicLink -Path ".claude\prompts\4. Retrospect for continuous improvement.md" -Target "$TEMPLATES_PATH\4. Act\4. Retrospect for continuous improvement.md"
```

### 4. Create `.claudeignore`

Create `.claudeignore` in your project root with patterns appropriate for your stack. Example:

```gitignore
# Build outputs
**/bin
**/obj
**/dist
**/build
node_modules/

# IDE and editor files
**/.vs
**/.idea
**/.vscode

# OS files
**/.DS_Store
**/Thumbs.db

# Test outputs
**/TestResults
**/*.trx
**/coverage/

# Logs
*.log

# Git
.git/
```

### 5. Create `.claude/instructions.md`

Create the main instructions file that Claude Code will read automatically (see section below).

### 6. Create `.claude/validation.md` (Optional)

Create a validation checklist for pre-commit checks (see section below).

## Configuration Files

### `.claude/instructions.md`

```markdown
# Project Development Workflow

This project follows a strict PDCA (Plan-Do-Check-Act) development process with TDD discipline.

## Workflow Phases

### Phase 1a: Analysis (MANDATORY FIRST)
- Execute codebase_search to discover existing patterns
- Validate external system formats before making assumptions
- Document architectural constraints
- Assess delegation complexity

### Phase 1b: Planning
- Create numbered, atomic implementation steps
- Define testing strategy (TDD with red-green-refactor)
- Identify integration touch points
- Plan for incremental delivery

### Phase 2: Test-Driven Implementation
**CRITICAL RULES:**
- ❌ DON'T test interfaces - test concrete implementations
- ❌ DON'T use compilation errors as RED phase
- ✅ DO write failing behavioral tests FIRST
- ✅ DO use real components over mocks
- Max 3 iterations per red-green cycle

### Phase 3: Completeness Check
- Verify all objectives met
- Audit process discipline
- Confirm no TODOs remain

### Phase 4: Retrospection
- Analyze critical moments
- Extract actionable insights
- Update working agreements

## Process Checkpoints
Before proceeding with implementation:
- [ ] Have I searched for similar implementations?
- [ ] Have I validated external system formats?
- [ ] Have I written a FAILING test first?
- [ ] Am I implementing ONLY enough to pass the test?

## Detailed Phase Instructions
See `.claude/prompts/` directory for detailed instructions for each phase.
```

### `.claude/validation.md`

```markdown
## Pre-Commit Validation Checklist

Before each commit, verify:

- [ ] Test was written and failed FIRST (true RED phase)
- [ ] Implementation makes test pass with minimal code
- [ ] No compilation-only reds (compilation errors don't count as RED)
- [ ] Using real components where possible (avoid unnecessary mocks)
- [ ] Following existing codebase patterns discovered in analysis
- [ ] TDD discipline maintained throughout (max 3 red-green iterations)
- [ ] Code is clean and refactored
- [ ] No TODOs or placeholder implementations remain
```

## Usage Workflow

### Starting a New Feature

Always work through phases sequentially:

#### Phase 1a: Analysis

```bash
claude "Following .claude/prompts/1a: Analyze implementing [feature description]. 
Search codebase for similar patterns before proposing approach. 
STOP after analysis and wait for approval."
```

**Review the analysis before proceeding.**

#### Phase 1b: Planning

```bash
claude "Based on approved analysis, create detailed implementation plan 
following .claude/prompts/1b. Break into atomic TDD steps."
```

**Review the plan and approve specific steps.**

#### Phase 2: Implementation (Step by Step)

```bash
# For each planned step:
claude "Test-drive step [N]: [specific requirement]. 
Follow .claude/prompts/2 TDD discipline strictly. 
Write failing test FIRST, then minimal implementation."
```

**Key points:**
- One step at a time
- Always RED (failing test) before GREEN (implementation)
- Review after each step before proceeding
- Maximum 3 red-green iterations per step

#### Phase 3: Completeness Check

```bash
claude "Run completeness check per .claude/prompts/3. 
Verify all planned steps complete and process followed."
```

#### Phase 4: Retrospection

```bash
claude "Retrospect on this implementation session following .claude/prompts/4. 
Identify what worked well and what to improve."
```

## Best Practices

### 1. Explicit Phase References
Always mention `.claude/prompts/[phase].md` in your commands so Claude knows where to look.

### 2. One Phase at a Time
Don't ask Claude to "implement feature X end-to-end". Break it into discrete phases.

### 3. Stop and Review
Use explicit STOP instructions after analysis and planning phases for human review.

### 4. Context Preservation
Use the same Claude Code conversation/task thread to maintain context across phases.

### 5. TDD Discipline Enforcement
If Claude strays from TDD discipline:
- Stop the task immediately
- Point out the specific violation
- Repost the relevant phase instructions
- Resume with corrected approach

### 6. Small, Testable Increments
Each implementation step should be:
- Completable in one TDD cycle
- Testable in isolation
- Additive (doesn't break existing tests)

## Troubleshooting

### Symlinks Not Working

**macOS/Linux:**
- Check that `git config core.symlinks` is true
- Verify you have write permissions to the project directory
- Try creating one symlink manually to test permissions

**Windows:**
- Verify Developer Mode is enabled
- Check that `git config core.symlinks` is true
- Ensure you're running PowerShell from the project root

### Claude Not Following Process
- Explicitly reference `.claude/prompts/[phase].md` in commands
- Break requests into smaller, phase-specific chunks
- Add "STOP and wait for approval" to prevent Claude from jumping ahead
- Review `.claude/instructions.md` - ensure it's clear and concise

### Tests Not Following TDD
- Verify you're requesting "failing test FIRST"
- Check that RED phase is behavioral failure, not compilation error
- Limit to 3 red-green iterations per step
- Reference `.claude/prompts/2` explicitly in implementation requests

### Context Loss Over Long Sessions
- Start new Claude Code task after 8-10 implementation steps
- Reference previous work: "Based on previous implementation of [X]..."
- Keep `.claude/instructions.md` concise so it's always in context

## Advanced: Multi-Project Setup

To use these prompts across multiple projects:

1. Keep your master prompts in a central location (e.g., iCloud, Dropbox, or a shared drive)
2. Create symlinks per project pointing to those masters
3. All projects stay in sync with your master PDCA templates

**macOS/Linux — shared script example:**
```bash
#!/bin/bash
# link-prompts.sh — run from your project root
TEMPLATES_PATH="${1:-$HOME/pdca-templates}"
mkdir -p .claude/prompts
for f in "1a Analyze to determine approach for achieving the goal" \
         "1b Create a detailed implementation plan"; do
  ln -sf "$TEMPLATES_PATH/1. Plan/$f.md" ".claude/prompts/$f.md"
done
# ... remaining phases
```

**Windows — shared script example:**
```powershell
# LinkPrompts.ps1 — run from your project root
param([string]$TemplatesPath = "C:\pdca-templates")
New-Item -ItemType Directory -Path ".claude\prompts" -Force
# ... symlink creation
```

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [PDCA Process Repository](https://github.com/kenjudy/pdca-framework)
- [claude-skill/README.md](claude-skill/README.md) — recommended skill-based setup

## License

This repository uses a dual license. Documentation and prompts — including all files in the phase directories and `Human Working Agreements.md` — are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source code — including all files in `claude-skill/` — is licensed under the [MIT License](https://opensource.org/licenses/MIT). See [LICENSE](LICENSE) for full terms.

**Attribution:** Ken Judy with Claude Anthropic

---

## Acknowledgments

The TDD content in this framework draws from several foundational sources:

- **[afbreilyn/afb-tdd](https://github.com/afbreilyn/afb-tdd)** (AFB Breilyn) -- stub design principle ("hardcode if possible, don't make it handle future scenarios"), Anti-Pattern #7 (Happy-Path Tunnel Vision), and the called-shot discipline of predicting the exact failure before running a test
- **[obra/superpowers](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)** (Jesse Vincent) -- Testing Anti-Patterns reference, adapted and extended for this framework
- **Kent Beck** -- *TDD by Example* (2002), "Canon TDD" (2023), *Tidy First?* (2023), *Refactoring* (1999), and "Test Desiderata": foundational TDD sequencing (Fake It / Obvious Implementation / Triangulate), the Starter Test principle, Two Hats doctrine, and the behavioral definition of unit tests
- **James Grenning** -- ZOMBIES test ordering (Zero/One/Many first), informing degenerate-case-first sequencing

obra/superpowers and afb-tdd are MIT licensed; content adapted from them is used with attribution as required. Beck and Grenning are cited as intellectual influences; no copyrighted text is reproduced from their published works.

---

*Last Updated: 2026*
