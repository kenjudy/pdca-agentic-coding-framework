---

# Beads Integration (Optional)

**If beads is configured**, store retrospective learnings for future cycles:

## Capture Retrospective

```bash
# Add retrospective to epic
bd update [epic-id] --append-notes "$(cat <<'EOF'
## Retrospective

**Session goal:** [original objective]

**What worked:**
- [Specific practices/decisions that accelerated progress]
- [Tools/patterns that proved valuable]

**What to improve:**
- [Process breakdowns or inefficiencies encountered]
- [Knowledge gaps that slowed implementation]

**Key insights:**
- [Architectural learnings]
- [Testing strategies discovered]
- [Gotchas to remember for similar features]

**Action items for next cycle:**
1. [Specific improvement to working agreements/prompts]
2. [Tool/setup to add]
3. [Pattern to reuse]
EOF
)"
```

## Tag and Close Epic

```bash
# Mark epic complete
bd close [epic-id]

# Optional: Add searchable metadata
bd update [epic-id] --metadata pdca_complete=true,domain=auth,complexity=medium
```

## Search Past Retrospectives

When starting new work, learn from past cycles:

```bash
# Find retrospectives about similar features
bd list --closed --type epic | grep -i [domain]

# Read full retrospective
bd show [epic-id]

# Find patterns
bd list --closed --metadata domain=auth
```

**Why use beads in ACT phase:**
- Retrospectives are searchable (not buried in chat history)
- Future PDCA cycles can reference past learnings
- Team members can discover solutions to similar problems
- Builds institutional knowledge over time

---

**PDCA Cycle Complete!**

Your analysis, implementation steps, and retrospective are now:
- ✓ Committed to git (.beads/) -- push when ready per working agreements
- ✓ Searchable via `bd` commands
- ✓ Preserved across sessions
- ✓ Available to future work

Run `bd list --closed --type epic` to see your completed PDCA cycles.
