# Beads Setup Guide

> Load this only when setting up beads for the first time.

**Optional Enhancement**: Beads is a git-backed issue tracker for persistent task tracking across PDCA sessions.

## What is Beads?

Beads provides:
- **Persistent memory** across Claude Code sessions
- **Dependency tracking** for task relationships
- **Git integration** with full audit trail
- **Cross-session continuity** for long-running development cycles

## Pre-flight Check

Before installing, verify what is already present:

```bash
which bd && bd --version || echo "bd not installed"
which dolt && dolt version || echo "dolt not installed"
brew outdated beads dolt
```

**If bd is installed and outdated:** `brew upgrade beads`
**If dolt is installed and outdated:** `brew upgrade dolt`
**If neither is installed:** proceed with Installation below.

Do not run `bd init` on an outdated install -- schema migrations can fail silently.

---

## System Requirements

**Required:**
- Go 1.23+ (install via `brew install go`)
- ICU headers (install via `brew install icu4c`)
- Dolt database (install via `brew install dolt`)

**Installation:**

```bash
# Install beads CLI with CGO support
ICU_PATH=$(brew --prefix icu4c@78)
export CGO_CFLAGS="-I${ICU_PATH}/include"
export CGO_CXXFLAGS="-I${ICU_PATH}/include"
export CGO_LDFLAGS="-L${ICU_PATH}/lib"
CGO_ENABLED=1 go install github.com/steveyegge/beads/cmd/bd@latest

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/go/bin:$PATH"

# Verify installation
bd --version
```

**Optional: MCP Server Integration**

Check whether beads-mcp is already installed and configured:

```bash
pip3 show beads-mcp 2>/dev/null && echo "installed" || echo "not installed"
grep -q '"beads"' ~/Library/Application\ Support/Claude/claude_desktop_config.json \
  && echo "configured in Claude" || echo "not in Claude config"
```

If not installed:

```bash
pip3 install beads-mcp
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "beads": {
      "command": "beads-mcp"
    }
  }
}
```

**Restart Claude Desktop/Code** after MCP configuration.

---

## When to Use Beads

**Use beads when:**
- PDCA cycle spans multiple sessions (days/weeks)
- Complex feature with many TDD steps to track
- Working on multiple related features (epics with subtasks)
- Want searchable retrospectives
- Collaborating across git repo

**Skip beads when:**
- Quick bug fix (single session)
- Simple 1-2 hour PDCA cycle
- Standalone script with no git repo
- Learning/experimenting (no need for persistence)

---

## Initializing Beads in a Project

Once tools are installed and you have decided to use beads for a project:

```bash
bd init    # creates .beads/ database; only needed once per repo
```

### Post-Init: Align CLAUDE.md with Working Agreements

`bd init` generates a project `CLAUDE.md` tuned for autonomous agents. If you are using human-in-the-loop supervision, patch it immediately after init.

Locate the `<!-- BEGIN BEADS INTEGRATION -->` block and make two changes:

**1. Replace the TaskCreate prohibition line:**

Remove:
> - Use `bd` for ALL task tracking -- do NOT use TodoWrite, TaskCreate, or markdown TODO lists

Replace with:
> - `bd` is available for cross-session issue tracking; use it alongside TaskCreate and standard tools

**2. Replace the Session Completion block:**

Remove the entire MANDATORY WORKFLOW section and CRITICAL RULES (everything between `## Session Completion` and `<!-- END BEADS INTEGRATION -->`).

Replace with:
> ## Session Completion
>
> Follow the global CLAUDE.md working agreements. Pushing and committing require explicit human confirmation per the global process discipline rules.

The quick reference commands (`bd ready`, `bd show`, `bd update`, `bd close`) should be kept unchanged -- they are informational, not behavioral mandates.

**3. Decide on a .beads/ sharing strategy:**

`bd init` may add `.beads/` to `.gitignore`. How you share beads data with collaborators determines what belongs in git.

**Option A: Git-native (commit JSONL bridge files)**

Beads writes human-readable JSONL files alongside the Dolt binary database. These are the git-friendly bridge. Keep `.beads/` excluded in `.gitignore` but allow the JSONL and config files:

```gitignore
.beads/
!.beads/.gitignore
!.beads/config.yaml
!.beads/metadata.json
!.beads/issues.jsonl
!.beads/interactions.jsonl
!.beads/hooks/
```

The binary `embeddeddolt/` data is Dolt's versioning territory -- do not commit it to git.

**Option B: Dolt-native (bd dolt push)**

Leave `.beads/` excluded from git entirely and share via Dolt's own remote:

```bash
bd dolt push   # push Dolt database to remote
bd dolt pull   # pull from remote on another machine
```

This requires configuring a Dolt remote for the project (see `bd help dolt`).

**Choosing:** Option A works with any git remote and gives readable diffs. Option B gives full Dolt commit history but requires a Dolt remote setup. Pick one per project -- do not mix.

---

## Troubleshooting

### "dolt: this binary was built without CGO support"

Install via Go with ICU headers (see System Requirements above).

### "bd: command not found"

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### MCP Server Not Showing in Claude

1. Verify `claude_desktop_config.json` has `mcpServers.beads`
2. Restart Claude Desktop/Code completely

### Beads Init Fails

```bash
brew install dolt && bd init --verbose
```

---

## License & Attribution

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Beads integration designed by [Ken Judy](https://github.com/kenjudy) with Claude Sonnet 4.5

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-agentic-coding-framework)
