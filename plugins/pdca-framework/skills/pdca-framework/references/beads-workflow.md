# Beads Workflow Reference

> Load this during active PDCA sessions when beads is installed.

## Prerequisites

If this is the first PDCA session in this repo, initialize beads before any other command:

```bash
bd init    # creates .beads/ database; only needed once per repo
```

`bd init` will fail with `no beads database found` if skipped. If beads is already initialized, this command is safe to re-run — it will report the existing configuration.

---

## Resume a Session

Before running any phase commands, orient yourself:

```bash
bd ready                              # unblocked open tasks
bd list --status in_progress          # anything claimed but not closed
bd show [epic-id]                     # full context if you have the epic ID
```

If you do not have the epic ID:

```bash
bd list --type epic --status open     # find open epics
```

Pick up from the last open `in_progress` task or the first `ready` task under your epic.

Also worth running at the start of any new PDCA cycle:

```bash
brew outdated beads dolt    # update if anything shows
```

---

## PDCA → Beads Mapping

| PDCA Phase | Beads Task Type | Purpose |
|------------|----------------|---------|
| **PLAN** | Epic | Capture analysis, store approach decisions |
| **DO** | Subtasks | Track individual TDD steps |
| **CHECK** | Verification | Validate completeness against plan |
| **ACT** | Retrospective | Store learnings for future cycles |

---

## Phase Workflows

### PLAN: Create Epic

```bash
bd create "Feature: [goal description]" --type epic
# Returns: [prefix]-a1b2 (your epic ID)

bd update [epic-id] --append-notes "$(cat <<'EOF'
## Analysis Summary
- [Key architectural patterns discovered]
- [Chosen approach and rationale]
- [Dependencies identified]

## Acceptance Criteria
- [ ] [Observable outcome 1 — user-visible or test-verifiable]
- [ ] [Observable outcome 2]
- [ ] [Edge cases explicitly handled or deferred]

## Out of Scope
- [What this cycle explicitly does NOT cover]

## Resumption Context
- Start point: [file:line or entry command to begin next session]
- Key constraint: [the thing most likely to trip up a fresh session]
- Open questions: [anything unresolved at session end, or "none"]
EOF
)"
```

**Save the epic ID** — you'll reference it in DO, CHECK, and ACT.

---

### DO: Track TDD Steps

**Before each TDD iteration:**

```bash
bd create "Step [N]: [description]" --parent [epic-id] --type task
bd update [task-id] --claim --status in_progress
bd update [task-id] --append-notes "$(cat <<'EOF'
Before: [current behavior or failing test name]
After: [expected behavior when this step is done]
Done when: [specific test passes or explicit verifiable condition]
EOF
)"
```

**After RED → GREEN → REFACTOR:**

```bash
bd close [task-id] --message "✓ Tests pass, committed [hash]"
```

**Review progress:**

```bash
bd list --parent [epic-id]
bd list --parent [epic-id] --status in_progress
```

---

### CHECK: Validate Completeness

```bash
bd list --parent [epic-id]                              # All subtasks
bd list --parent [epic-id] --status open,in_progress    # Incomplete work
bd show [epic-id]                                       # Full context
```

All planned subtasks closed? No tasks in-progress? → Proceed to ACT.

---

### ACT: Store Retrospective

```bash
bd update [epic-id] --append-notes "$(cat <<'EOF'
## Retrospective
**What worked:** [practices that accelerated progress]
**What to improve:** [process breakdowns or inefficiencies]
**Key insights:** [architectural learnings, gotchas]
**Action items:** [1-3 improvements for next cycle]
EOF
)"

bd close [epic-id]
```

---

## Cross-Session Continuity

```bash
bd ready          # Tasks with no blockers
bd show [epic-id] # Full context: analysis, subtasks, messages, dependencies
```

---

## Common Commands

```bash
# Create
bd create "Title" --type epic|task|bug|feature
bd create "Subtask" --parent <id>

# Manage
bd ready                        # No-blocker tasks
bd list --status open           # Filter by status
bd show <id>                    # Detail view
bd update <id> --status in_progress
bd close <id>

# Dependencies (type defaults to "blocks" — do not pass it as a positional arg)
bd dep add <blocked-issue-id> <blocker-issue-id>
bd blocked

# Search past cycles
bd list --closed --type epic | grep -i [domain]
```

---

## Export Requirements Document

Generate a structured markdown document from all open epics and their tasks (open or closed). Useful for handoffs, reviews, and planning the next PDCA cycle.

```bash
bash .claude/skills/pdca-framework/references/scripts/export-requirements.sh requirements.md
```

The script uses `bd graph --all --compact` for a dependency overview, then iterates all open epics and their child tasks via `bd show`.

**Slash command (optional):** Add the following as `.claude/commands/requirements-doc.md` in your project to get `/requirements-doc`:

```markdown
Generate a requirements document from all open beads epics and their tasks.

Run:
```bash
bash .claude/skills/pdca-framework/references/scripts/export-requirements.sh requirements.md
```

Then present the contents of requirements.md to the user.
```

---

## Git Integration

Commit `.beads/` changes like any other project file. Beads data lives in `.beads/` and should be committed alongside the code it tracks:

```bash
git add .beads/
git commit -m "chore: update beads tracking for [epic-id]"
```

Pushing is human-initiated per working agreements. Do not push on behalf of the user unless explicitly asked.
