# PDCA Framework Skills - Setup Guide

A Claude skill for human-supervised AI-assisted code generation using Plan-Do-Check-Act methodology.

> To generate a custom AI workflow skill for any domain, see [ai-workflow-builder](https://github.com/kenjudy/ai-workflow-builder).

---

## pdca-framework — AI-Assisted Code Generation

A disciplined framework for AI-assisted code generation with strict TDD:
- Maintains code quality through structured TDD practices
- Reduces technical debt by enforcing architecture pattern discovery
- Keeps humans actively engaged and accountable
- Provides structured prompts for analysis, planning, implementation, validation, and retrospection

**Based on research showing:** AI code generation without human oversight leads to 10x increase in duplicated code, 7.2% decrease in delivery stability, and 19% slower development.

---

## 📦 Skill Package

**pdca-framework.skill** includes:
- ✅ Core PDCA framework (Plan→Do→Check→Act)
- ✅ Strict TDD discipline and working agreements
- ✅ Beads integration files included (optional)
- 📦 **Size**: ~20K

**Beads** (by [Steve Yegge](https://github.com/steveyegge)) adds persistent task tracking across sessions. Optional — see [Beads Integration](#beads-integration) if you want it.

---

## Installation

**Most users should download the pre-built skill from [GitHub Releases](https://github.com/kenjudy/pdca-agentic-coding-framework/releases/latest)** rather than building from source. If you need the latest unreleased changes from `main` or are customizing the prompts, see the "Alternative: Install via Script" steps below (Claude Code or Codex) — they build from source before installing.

**Important:** Claude.ai (web/desktop), Claude Code, and Codex use different installation methods.

### For Claude.ai Web/Desktop App (Skill Upload)

This is the primary distribution path — upload `pdca-framework.skill` directly in Claude's UI.

1. **Download the skill file**
   - [**Download pdca-framework.skill**](https://github.com/kenjudy/pdca-agentic-coding-framework/releases/latest/download/pdca-framework.skill) (latest release)
   - Or build from source: `cd skill && bash build-skill.sh`

2. **Open Claude Settings**
   - Go to [claude.ai](https://claude.ai) or open the Claude desktop app
   - Click **Customize** in the left sidebar (or your profile menu)
   - Select **Skills**

3. **Upload the skill**
   - Click **Add Skill**
   - Select `pdca-framework.skill`
   - Confirm the upload

4. **Enable the skill**
   - The skill appears in your skills list — toggle it on
   - Verify it shows as active

> **Org/team distribution:** Enterprise and Team plan admins can provision skills for their
> organization via the admin console. See Anthropic's
> [Skills for organizations](https://support.claude.com) documentation.

**Note:** To enable beads, see [Beads Integration](#beads-integration). The skill works without it.

### For Claude Code (Command Line)

Claude Code uses a **directory-based** skill format, not the `.skill` package file.

[Download `pdca-framework.skill` from Releases](https://github.com/kenjudy/pdca-agentic-coding-framework/releases/latest) first.

#### Install - Personal Skills (Available Across All Projects)

Just the downloaded `.skill` file — no repo clone needed:

**macOS/Linux (Bash):**
```bash
# Create the parent directory
mkdir -p ~/.claude/skills

# Extract the skill package (zip contains pdca-framework/ at root)
unzip pdca-framework.skill -d ~/.claude/skills

# Result:
# ~/.claude/skills/pdca-framework/
#   ├── SKILL.md
#   └── references/
#       ├── plan-prompts.md
#       ├── do-prompts.md
#       ├── check-prompts.md
#       ├── act-prompts.md
#       ├── working-agreements.md
#       ├── plan-beads-addon.md    (optional — beads phase steps)
#       ├── do-beads-addon.md
#       ├── check-beads-addon.md
#       ├── act-beads-addon.md
#       ├── beads-setup.md         (optional — first-time beads install)
#       └── beads-workflow.md      (optional — per-session beads reference)
```

**Windows (PowerShell):**
```powershell
# Create the parent directory
New-Item -ItemType Directory -Path "$HOME\.claude\skills" -Force | Out-Null

# Extract the skill package (zip contains pdca-framework/ at root)
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("pdca-framework.skill", "$HOME\.claude\skills")

# Result: same pdca-framework/ layout as above, under %USERPROFILE%\.claude\skills\
```

#### Install - Project Skill (Shared with Team via Git)

Use this instead of the personal install above when the skill should travel with a specific repo rather than depend on each teammate remembering to install it themselves. Claude Code auto-discovers skills committed under `.claude/skills/` in a project (no config needed), so anyone who clones the repo and runs `claude` there gets the PDCA workflow automatically — useful when a team wants to standardize how a particular codebase is worked on, not just how one person works everywhere. The tradeoff: it's scoped to this one repo (personal installs at `~/.claude/skills/` apply everywhere), and first-time cloners will see a one-time workspace-trust prompt for the committed `.claude/` config.

**macOS/Linux (Bash):**
```bash
# From your project directory
mkdir -p .claude/skills

# Extract the skill package (zip contains pdca-framework/ at root)
unzip /path/to/pdca-framework.skill -d .claude/skills

# Commit to share with team
git add .claude/skills/
git commit -m "Add PDCA framework skill"
```

**Windows (PowerShell):**
```powershell
# From your project directory
New-Item -ItemType Directory -Path ".claude\skills" -Force | Out-Null

# Extract the skill package (zip contains pdca-framework/ at root)
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("C:\path\to\pdca-framework.skill", ".claude\skills")

# Commit to share with team
git add .claude/skills/
git commit -m "Add PDCA framework skill"
```

#### Alternative: Install via Script (Repo Clone Only)

If you've cloned the repo (e.g. to build from source), `install-skill.sh` / `install-skill.ps1` wraps the same unzip steps and prompts for scope:

**macOS/Linux (Bash):**
```bash
# From the skill directory
./build-skill.sh

# Optional: Specify scope as argument
./install-skill.sh personal   # Install to ~/.claude/skills/ (default)
./install-skill.sh project    # Install to current project's .claude/skills/
./install-skill.sh codex      # Install to ~/.agents/skills/
```

**Windows (PowerShell):**
```powershell
# From the skill directory
.\build-skill.ps1

# Optional: Specify scope as argument
.\install-skill.ps1 personal   # Install to ~/.claude/skills/ (default)
.\install-skill.ps1 project    # Install to current project's .claude/skills/
.\install-skill.ps1 codex      # Install to %USERPROFILE%\.agents\skills\
```

See [BUILD.md](BUILD.md) for full details, including troubleshooting and CI/CD automation.

#### Verify Installation

**macOS/Linux (Bash):**
```bash
# For personal skills
ls ~/.claude/skills/pdca-framework/

# For project skills
ls .claude/skills/pdca-framework/

# Should show: SKILL.md and references/
```

**Windows (PowerShell):**
```powershell
# For personal skills
dir "$HOME\.claude\skills\pdca-framework\"

# For project skills
dir ".claude\skills\pdca-framework\"

# Should show: SKILL.md and references/
```

**Note:** Skills are automatically discovered by Claude Code. No restart needed.

---

### For Codex (Command Line)

Codex discovers personal skills from `~/.agents/skills/`.

[Download `pdca-framework.skill` from Releases](https://github.com/kenjudy/pdca-agentic-coding-framework/releases/latest) first.

#### Install - Personal Skills

**macOS/Linux (Bash):**
```bash
mkdir -p ~/.agents/skills
unzip pdca-framework.skill -d ~/.agents/skills
ls ~/.agents/skills/pdca-framework/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.agents\skills" -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("pdca-framework.skill", "$env:USERPROFILE\.agents\skills")
dir "$env:USERPROFILE\.agents\skills\pdca-framework\"
```

#### Alternative: Install via Script (Repo Clone Only)

```bash
# macOS/Linux — from the skill directory
cd skill
./build-skill.sh
./install-skill.sh codex
```

```powershell
# Windows — from the skill directory
cd skill
.\build-skill.ps1
.\install-skill.ps1 codex
```

See [BUILD.md](BUILD.md) for full details, including troubleshooting and CI/CD automation.

---

## Quick Start

### Starting a New Coding Session

Simply mention your coding task and the skill will auto-trigger:

```
I need to add a new payment validation feature to our checkout flow. 
Let's use the PDCA framework.
```

Or explicitly reference the skill:

```
@pdca-framework I need to fix a bug in the user authentication system.
```

### Following the PDCA Cycle

The skill will guide you through four phases:

#### 1. **PLAN** (7-15 min)
Claude will prompt you through:
- **Analysis**: Understanding the problem and discovering existing patterns
- **Planning**: Creating atomic, testable implementation steps

#### 2. **DO** (30 min - 2.5 hrs)
Claude will provide:
- **TDD checklists**: Red-green-refactor discipline
- **Integration guidance**: Real components over mocks
- **Process checkpoints**: When to pause and validate

#### 3. **CHECK** (2-5 min)
Claude will verify:
- **Completeness**: All objectives met
- **Quality**: Tests passing, no regressions
- **Process compliance**: TDD maintained throughout

#### 4. **ACT** (5-10 min)
Claude will facilitate:
- **Retrospective**: What worked, what didn't
- **Improvements**: 1-3 changes for next cycle
- **Learning capture**: Update working agreements

---

## Using Specific Phases

### Get Analysis Prompt
```
@pdca-framework Show me the analysis phase prompt
```

### Get Planning Prompt
```
@pdca-framework I need the detailed planning template
```

### Get TDD Implementation Checklist
```
@pdca-framework Show me the DO phase checklist
```

### Run a Retrospective
```
@pdca-framework Let's retrospect on this session
```

---

## Working Agreements

The skill includes working agreements that define your collaboration contract with the AI. Key principles:

- **USE TDD FOR CHANGES** - Intervene when agent breaks discipline
- **One change at a time** - No fixing multiple things simultaneously
- **Respect existing architecture** - Work within established patterns
- **Process discipline trumps immediate progress** - Stop and correct violations

These are stored in the skill and referenced automatically, but you can also review them:

```
@pdca-framework Show me the working agreements
```

---

## Customizing for Your Team

### Step 1: Export the Skill Contents
Ask Claude to show you the current prompt templates:
```
@pdca-framework Show me the [PLAN/DO/CHECK/ACT] phase prompts
```

### Step 2: Identify Changes
Based on your retrospectives, determine what needs updating:
- Language-specific testing patterns (pytest, jest, xUnit, etc.)
- Your team's architectural conventions
- Project-specific quality gates
- Intervention triggers that work for your team

### Step 3: Document Your Changes
Keep a working document of your customizations:
```markdown
## Our Team's PDCA Customizations

### Analysis Phase
- Added: Terraform state validation check
- Changed: "codebase_search" → our internal tool name

### TDD Implementation
- Added: Our cypress integration test pattern
- Removed: References to unit test patterns we don't use
```

### Step 4: Request Skill Updates
When you have 3-5 meaningful changes:
```
@pdca-framework Based on our retrospectives, I want to update the 
analysis phase to include [specific change]. Can you help me create 
an updated version of this skill?
```

---

## Troubleshooting

### Skill Not Triggering
**Symptoms:** Claude doesn't use the framework when discussing code

**Solutions:**
1. Explicitly reference it: `@pdca-framework`
2. Use trigger words: "code generation", "TDD", "PDCA cycle"
3. Check skill is enabled in settings

### Context Drift During DO Phase
**Symptoms:** Agent makes sprawling changes, ignores TDD, breaks rules

**Solution:** This is expected behavior when context window fills. Follow the skill's recovery process:
1. Stop the thread immediately
2. Tell Claude what you observe
3. Say: `@pdca-framework I'm seeing context drift. Let's refocus on step [X] using the DO phase checklist`

### Too Much Boilerplate
**Symptoms:** Prompts feel repetitive or verbose

**Solution:** The skill is designed for 1-3 hour coding sessions. For very small changes:
```
@pdca-framework Quick mode - I just need to [simple change]. 
Skip to DO phase with minimal planning.
```

### Agent Suggests Non-TDD Approach
**Symptoms:** Claude proposes skipping tests or making large changes

**Solution:** Invoke your working agreements:
```
Stop. Our working agreement is to use TDD. Show me the failing test first.
```

---

## Best Practices

### 1. Right-Size Your Sessions
- **Ideal:** 1-3 hours of focused work
- **Too small:** < 30 minutes (overhead > value)
- **Too large:** > 3 hours (context drift likely)

### 2. Run Daily Retrospectives
After each session:
```
@pdca-framework Let's retrospect on today's work
```
Make 1-3 small improvements, not wholesale changes.

### 3. Keep Working Agreements Visible
Print or display your working agreements during coding sessions. They're your intervention triggers.

### 4. Intervene Early and Often
Don't wait for big problems:
- "You're on step 3 but this looks like step 5 work"
- "Did you write the failing test first?"
- "Are we respecting the existing FileProvider pattern?"

### 5. Use Real Components in Tests
Question any mocking:
```
Why are we mocking the file system? 
Can we use a temporary directory instead?
```

---

## When NOT to Use This Skill

The PDCA framework is designed for **production code generation**. Don't use it for:

- **Exploratory coding** - Quick experiments, prototypes
- **Documentation writing** - README files, API docs
- **Configuration changes** - YAML, JSON, environment files
- **Trivial changes** - Typo fixes, import reordering
- **Learning exercises** - Tutorials, katas, practice problems

For these tasks, regular Claude conversation is more appropriate.

---

## Learning More

### Understanding the Research
The skill is based on documented research showing AI code generation quality issues:
- GitClear 2024: 10x increase in duplicated code
- Google DORA 2024: 7.2% stability decrease per 25% AI adoption
- METR 2025: 19% slower development with AI tools

Read the full framework paper: [SOSA 2025 Notes](https://github.com/kenjudy/pdca-agentic-coding-framework/blob/main/presentations/SOSA%202025/SOSA%202025%20Notes.md)

Presentation prepared for [XP 2026](https://kenjudy.us/presentations/human-centric-ai-code-generation/)

### Philosophy
This framework embodies agile principles:
- **Individuals and interactions** over processes and tools (human oversight)
- **Working software** over comprehensive documentation (TDD focus)
- **Customer collaboration** over contract negotiation (value-based objectives)
- **Responding to change** over following a plan (retrospection)

### Contributing
The PDCA framework is open source under a dual license: CC BY 4.0 for documentation and prompts, MIT for source code.

**Repository:** https://github.com/kenjudy/pdca-agentic-coding-framework
**Issues/Suggestions:** [Create GitHub issue](https://github.com/kenjudy/pdca-agentic-coding-framework/issues/new)
**Discussions:** [GitHub Discussions](https://github.com/kenjudy/pdca-agentic-coding-framework/discussions)

---

## Support

### Getting Help
1. Check this README first
2. Review the changelog for recent updates
3. Try asking Claude: `@pdca-framework Explain [concept]`
4. Open an issue on GitHub

### Sharing Your Experience
Help improve the framework:
- Share retrospective insights
- Document what customizations work
- Report bugs or unclear guidance
- Suggest improvements

---

## Version Information

**Current Version:** v1.1.0
**License:** CC BY 4.0 (documentation & prompts) / MIT (source code)
**Attribution:** Ken Judy with Claude Anthropic 4
**Last Updated:** 2026-05-28

---

## Quick Reference Card

```markdown
PDCA CYCLE QUICK REFERENCE

1. PLAN (7-15 min)
   └─ Analysis: Discover patterns, validate external systems
   └─ Planning: Create atomic steps, define testing strategy

2. DO (30 min - 2.5 hrs)
   └─ Red: Write failing test
   └─ Green: Minimal code to pass
   └─ Refactor: Clean up
   └─ Repeat for each step

3. CHECK (2-5 min)
   └─ All tests passing?
   └─ Process discipline maintained?
   └─ Ready to close?

4. ACT (5-10 min)
   └─ What worked?
   └─ What didn't?
   └─ What to change next time?

INTERVENTION TRIGGERS
- No failing test first → "Where's the red?"
- Multiple changes → "One thing at a time"
- Breaking patterns → "Are we following [existing pattern]?"
- Context drift → Stop, refocus, restart

HUMAN COMMITMENTS
✓ Intervene early and often
✓ Take accountability for code quality
✓ Make 1-3 improvements per cycle
✓ Stay engaged throughout session
```

Print this card and keep it visible during coding sessions!

---

## Development Setup

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/) (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### For running unit tests (no API key needed)

```bash
cd skill
uv sync --extra test
bash run-tests.sh
```

### For running eval tests (requires Anthropic API key, ~$2-5/full run)

LLM-as-judge evaluations check whether each PDCA phase prompt produces compliant responses
across a range of scenarios. Claude Haiku acts as the judge, scoring outputs against a
chain-of-thought rubric (strengths → weaknesses → reasoning → score).

```bash
cd skill
uv sync --extra eval
cp .env.example .env          # add your ANTHROPIC_API_KEY
bash run-evals.sh             # run all prompt evals
```

To run a single prompt's evals:

```bash
bash run-evals.sh tests/test_evals.py::TestPrompt1aEvals
```

Eval tests are tagged `@pytest.mark.eval` and are **excluded from the default test suite**.
They are not run in CI — invoke manually when iterating on phase prompt quality.

> **Note:** Unit tests (`run-tests.sh`) run in CI on every push. Eval tests cost API tokens
> and are intentionally on-demand only.

---

## Beads Integration

**Optional** — the skill works without beads. Set it up when you want persistent task tracking across multi-day sessions. Beads is created by [Steve Yegge](https://github.com/steveyegge).

All beads commands in the prompts are optional. The skill includes `references/beads-setup.md` (first-time install guide) and `references/beads-workflow.md` (per-session reference) that Claude loads only when needed.

### Understanding Global Skill vs. Per-Project Beads

**Important distinction:**

| Component | Location | Scope | Purpose |
|-----------|----------|-------|---------|
| **Skill Installation** | `~/.claude/skills/pdca-framework-beads/` | Global | PDCA prompts available in all projects |
| **Beads Database** | `.beads/` in each project root | Per-Project | Task tracking for THAT project only |

**You install the skill once globally, but initialize beads separately in each project.**

**Why per-project beads?**
- PDCA cycles are project-specific (features, bugs, experiments for that codebase)
- Retrospectives make sense in project context ("How did auth work in THIS app?")
- Searching is more relevant: `bd list --closed` shows THIS project's history
- Team collaboration: share issue history via git (JSONL files) or Dolt remote (`bd dolt push`)
- Clean separation: No mixing dashboard tasks with unrelated projects

**Why NOT one global beads database?**
- Searching "authentication retrospectives" would return ALL projects (too noisy)
- Epic/task organization becomes confusing across codebases
- Can't scope queries to relevant work
- Can't share project-specific retrospectives via git

**The architecture:**
1. Install skill globally (once) → prompts available everywhere
2. Initialize beads per-project → task tracking scoped to that project
3. When working in a project, the global skill prompts guide you to use that project's local `.beads/` database

### Prerequisites

**System Requirements:**
```bash
# Required
brew install go icu4c dolt

# Verify versions
go version    # Should be 1.23+
dolt version  # Should be 1.80+
```

### Installation Steps

#### 1. Install Beads CLI

```bash
# Set ICU paths for compilation
ICU_PATH=$(brew --prefix icu4c@78)
export CGO_CFLAGS="-I${ICU_PATH}/include"
export CGO_CXXFLAGS="-I${ICU_PATH}/include"
export CGO_LDFLAGS="-L${ICU_PATH}/lib"

# Install beads with CGO support
CGO_ENABLED=1 go install github.com/steveyegge/beads/cmd/bd@latest

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/go/bin:$PATH"

# Verify installation
bd --version
```

**⚠️ Always use this CGO build method to upgrade beads.** The `curl | bash` install script that `bd doctor` recommends installs a prebuilt binary *without* CGO support. That binary cannot open the Dolt database and will break beads entirely. To upgrade: re-run the `CGO_ENABLED=1 go install` command above.

#### 2. Install Beads MCP Server (Optional but Recommended)

```bash
# Install beads MCP server
pip3 install beads-mcp

# Configure in Claude Desktop/Code
# Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "beads": {
      "command": "beads-mcp"
    }
  }
}

# Restart Claude Desktop/Code after configuration
```

#### 3. Initialize Beads Per-Project (Repeat for Each Project)

**Important:** Run this in EACH project where you want beads tracking, not just once globally.

```bash
# Navigate to your project
cd /path/to/your/project

# Initialize beads (creates .beads/ in THIS project)
bd init

# Created: .beads/ directory (local to this project)
```

**Example:** If you work on 3 projects:
```bash
cd ~/Projects/dashboard && bd init      # Creates ~/Projects/dashboard/.beads/
cd ~/Projects/api && bd init            # Creates ~/Projects/api/.beads/
cd ~/Projects/frontend && bd init       # Creates ~/Projects/frontend/.beads/
```

Each project gets its own independent beads database for tracking its PDCA cycles.

#### 4. Choose a .beads/ sharing strategy

`bd init` may add `.beads/` to `.gitignore`. Decide how you want to share beads data with collaborators:

**Option A: Git-native (commit JSONL bridge files)**

Keep `.beads/` excluded but allow the JSONL files that serve as the git-friendly bridge. Add to `.gitignore`:

```gitignore
.beads/
!.beads/.gitignore
!.beads/config.yaml
!.beads/metadata.json
!.beads/issues.jsonl
!.beads/interactions.jsonl
!.beads/hooks/
```

The binary `embeddeddolt/` data is Dolt's own versioning territory -- do not commit it to git.

**Option B: Dolt-native (bd dolt push)**

Leave `.beads/` excluded from git and share via Dolt's remote:

```bash
bd dolt push   # push to Dolt remote
bd dolt pull   # pull on another machine
```

See `references/beads-setup.md` for the full post-init checklist including CLAUDE.md alignment.

### Using Beads with PDCA

Each PDCA phase includes optional beads sections in the prompts. Example workflow:

**PLAN Phase:**
```bash
# Create epic for this PDCA cycle
bd create "Feature: Add user authentication" --type epic
# Returns: myproject-a1b2
```

**DO Phase:**
```bash
# Track each TDD step
bd create "Step 1: Write failing test for JWT middleware" --parent myproject-a1b2
bd update myproject-a1b2.1 --claim --status in_progress

# After tests pass
bd close myproject-a1b2.1 --message "✓ Tests pass, committed abc123"
```

**CHECK Phase:**
```bash
# Verify all tasks complete
bd list --parent myproject-a1b2 --status open,in_progress
```

**ACT Phase:**
```bash
# Store retrospective
bd update myproject-a1b2 --append-notes "Retrospective: TDD kept scope focused..."
bd close myproject-a1b2
```

### Benefits of Beads Integration

- **Cross-session continuity**: Resume work days/weeks later with `bd show <epic-id>`
- **Dependency tracking**: `bd dep add <task> <blocker> blocks`
- **Searchable retrospectives**: `bd list --closed --type epic | grep auth`
- **Git-backed audit trail**: Issues committed as `.beads/issues.jsonl` (travels with your repo)

### Troubleshooting Beads

**"bd: command not found"**
- Add `$HOME/go/bin` to your PATH
- Verify installation: `ls ~/go/bin/bd`

**"dolt: this binary was built without CGO support"**
- Reinstall beads with CGO flags (see Installation Step 1)
- Ensure ICU headers are installed: `brew install icu4c`

**"invalid database name: beads_Your Project" (spaces in project path)**
- Beads v0.59+ rejects database names with spaces (derived from the project directory name)
- Rename the Dolt database directory: `mv .beads/dolt/"beads_Your Project" .beads/dolt/beads_Your_Project`
- Update `.beads/metadata.json`: change `"dolt_database"` to match the new name (underscores)
- Restart the Dolt server: `bd dolt stop && bd dolt start`
- Run `bd doctor --fix` to clean up any remaining issues

**MCP server not showing**
- Verify `claude_desktop_config.json` has `mcpServers.beads`
- Restart Claude Desktop/Code completely
- Check for MCP errors in Claude logs

For detailed beads documentation, see:
- `references/beads-setup.md` — first-time installation and MCP configuration
- `references/beads-workflow.md` — per-phase commands for active sessions

---

**Ready to start?** Try: `@pdca-framework I need to [your coding task]`
