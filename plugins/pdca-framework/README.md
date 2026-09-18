# PDCA Framework — Per-Phase Slash Commands

Five thin router commands that let you invoke a single PDCA phase directly, instead of
only the full-cycle `/pdca-framework` skill:

| Command | Phase |
|---|---|
| `/pdca` | Full cycle (Plan → Do → Check → Act) — alias for the `pdca-framework` skill |
| `/pdca-plan` | PLAN only — sequences 1a Analysis, then 1b Detailed Planning |
| `/pdca-do` | DO only — TDD implementation with active oversight |
| `/pdca-check` | CHECK only — completeness validation |
| `/pdca-act` | ACT only — retrospective and continuous improvement |

Each command is a thin router: it names its phase's section in `SKILL.md` and points at
that phase's `references/*.md` file(s) rather than duplicating their content, and each of
the four single-phase commands explicitly refuses to proceed into the other phases in the
same turn.

**Prerequisite:** these commands require the `pdca-framework` skill to already be
installed and active (see [../../skill/README.md](../../skill/README.md)). They are a
convenience layer on top of the skill, not a replacement for it — a command invoked
without the skill installed will say so rather than silently failing.

## Install

The files in [`commands/`](commands/) here are the versioned source of truth. Copy or
symlink them into a directory Claude Code already auto-discovers:

**Personal (all projects) — macOS/Linux:**
```bash
mkdir -p ~/.claude/commands
cp plugins/pdca-framework/commands/*.md ~/.claude/commands/
```

**Personal (all projects) — Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Path "$HOME\.claude\commands" -Force | Out-Null
Copy-Item plugins\pdca-framework\commands\*.md "$HOME\.claude\commands\"
```

**Project-scoped (shared with a team via git), from that project's root:**
```bash
mkdir -p .claude/commands
cp /path/to/pdca-agentic-coding-framework/plugins/pdca-framework/commands/*.md .claude/commands/
git add .claude/commands/
git commit -m "Add PDCA per-phase slash commands"
```

**Try it without copying, for this session only:**
```bash
claude --plugin-dir plugins/pdca-framework
```
This loads the commands as a Claude Code plugin for the current session — useful for
trying them out, but not persistent across sessions the way copying into
`~/.claude/commands/` is.

**Note on plugin marketplace distribution:** this directory is laid out as a Claude Code
plugin (`.claude-plugin/plugin.json`) so it can be referenced by a marketplace catalog
that lists it via git-subdir source — this repo does not host its own marketplace catalog
(no root-level `.claude-plugin/marketplace.json`), so `claude plugin marketplace add` does
not work directly against this repo today. The copy/symlink method above is the supported
install path until a marketplace listing exists.

## Verify

```bash
ls ~/.claude/commands/pdca*.md   # or .claude/commands/ for a project install
```

Then in a Claude Code session, `/pdca-plan` (etc.) should appear as an available slash
command. **A fresh session is required** — command definitions load once per session, so
editing an already-loaded command file will not update mid-session; re-check in a newly
started session before trusting an edit.
