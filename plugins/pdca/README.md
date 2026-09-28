# PDCA Framework — Claude Code Plugin

A self-contained Claude Code plugin bundling the `pdca-framework` skill (`skills/pdca-framework/`,
built from the same masters as `pdca-framework.skill`) and five thin router commands that
invoke a single PDCA phase directly instead of the full cycle:

| Command (marketplace install) | Command (manual copy) | Phase |
|---|---|---|
| `/pdca-framework:pdca` | `/pdca` | Full cycle (Plan → Do → Check → Act) — alias for the `pdca-framework` skill |
| `/pdca-framework:pdca-plan` | `/pdca-plan` | PLAN only — sequences 1a Analysis, then 1b Detailed Planning |
| `/pdca-framework:pdca-do` | `/pdca-do` | DO only — TDD implementation with active oversight |
| `/pdca-framework:pdca-check` | `/pdca-check` | CHECK only — completeness validation |
| `/pdca-framework:pdca-act` | `/pdca-act` | ACT only — retrospective and continuous improvement |

Claude Code namespaces a plugin's commands under the plugin's own name, so a marketplace
install (below) resolves the qualified form on the left; a manual copy into
`~/.claude/commands/` resolves the bare form on the right. Use whichever column matches
how you installed.

Each command is a thin router: it names its phase's section in `SKILL.md` and points at
that phase's `references/*.md` file(s) rather than duplicating their content, and each of
the four single-phase commands explicitly refuses to proceed into the other phases in the
same turn.

## Install

**Recommended: via the self-hosted marketplace** (see [`../../.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)) —
installs the skill and all five commands in one step, no separate skill install needed:

```bash
claude plugin marketplace add kenjudy/pdca-agentic-coding-framework
claude plugin install pdca
```

**Already have the skill installed manually?** Remove the old copies first to avoid
running two side by side — see [../../skill/README.md](../../skill/README.md)'s
Claude Code install section for the exact paths to remove.

### Alternative: commands only, skill installed separately

If you only want the router commands — say, because you're installing the skill via
`skill/install-skill.sh` rather than the plugin marketplace — `install-skill.sh` (or
`install-skill.ps1` on Windows) installs these commands automatically alongside the
skill, no manual copy step required:

```bash
cd skill
./build-skill.sh
./install-skill.sh personal   # or: project, codex
```

This places the five command files in `~/.claude/commands/` (personal), the current
project's `.claude/commands/` (project), or `~/.codex/prompts/` (codex) — whichever the
chosen scope's platform auto-discovers. Note the commands reference the skill by its bare
name (`pdca-framework`), so they resolve regardless of which install path put the skill
in place.

### Manual install

The files in [`commands/`](commands/) here are the versioned source of truth. If you're
not running the installer (e.g. iterating on a command file directly), copy or symlink
them yourself into a directory Claude Code already auto-discovers:

**Personal (all projects) — macOS/Linux:**
```bash
mkdir -p ~/.claude/commands
cp plugins/pdca/commands/*.md ~/.claude/commands/
```

**Personal (all projects) — Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Path "$HOME\.claude\commands" -Force | Out-Null
Copy-Item plugins\pdca\commands\*.md "$HOME\.claude\commands\"
```

**Project-scoped (shared with a team via git), from that project's root:**
```bash
mkdir -p .claude/commands
cp /path/to/pdca-agentic-coding-framework/plugins/pdca/commands/*.md .claude/commands/
git add .claude/commands/
git commit -m "Add PDCA per-phase slash commands"
```

**Try it without copying, for this session only:**
```bash
claude --plugin-dir plugins/pdca
```
This loads the whole plugin (skill and commands) for the current session — useful for
trying it out, but not persistent across sessions the way `claude plugin install` or
copying into `~/.claude/commands/` is.

**Note:** this manual copy method only places the commands — it does not install the
skill they route to. Use the marketplace install above for a self-contained setup, or
install the skill separately via `skill/install-skill.sh` first.

## Verify

**Marketplace install:**
```bash
claude plugin list
```
Should show `pdca@<marketplace-name>` enabled. Then in a Claude Code session,
`/pdca:pdca-plan` (etc.) should appear as an available slash command.

**Manual copy install:**
```bash
ls ~/.claude/commands/pdca*.md   # or .claude/commands/ for a project install
```
Then in a Claude Code session, `/pdca-plan` (etc.) should appear as an available slash
command.

**Either way, a fresh session is required** — command definitions load once per session, so
editing an already-loaded command file will not update mid-session; re-check in a newly
started session before trusting an edit.
