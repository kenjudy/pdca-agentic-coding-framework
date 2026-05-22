---

# Beads Integration (Optional)

**If beads is configured**, track this PDCA cycle with persistent tasks:

## Create Epic for This Cycle

```bash
# Create epic to track this PDCA cycle
bd create "Feature: [goal description]" --type epic

# Example: bd create "Feature: Add user authentication" --type epic
# Returns: [prefix]-a1b2 (your epic ID)
```

## Capture Analysis Notes

After completing your analysis, store key decisions:

```bash
# Add analysis summary to epic
bd update [epic-id] --append-notes "$(cat <<'EOF'
## Analysis Summary
- [Key architectural patterns discovered]
- [Chosen approach and rationale]
- [Dependencies identified]
- [Complexity assessment]

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

## Create CHECK and ACT Tasks

After finalizing the plan, create tasks for the verification and retrospective steps:

```bash
# CHECK task — always required
bd create "CHECK: Verify [goal] against acceptance criteria" --parent [epic-id] --type task

# ACT task — always required
bd create "ACT: Retrospective and working agreement updates" --parent [epic-id] --type task
```

These tasks appear in the task graph alongside implementation steps so CHECK can verify completeness against the full plan.

**Why use beads in PLAN phase:**
- Preserves analysis across sessions
- Creates audit trail of decision rationale
- Provides context for resuming work later
- Links dependencies between features

**Save the epic ID** - you'll reference it in DO, CHECK, and ACT phases.

---

**Next**: Proceed to Planning phase (1b), then move to DO phase with your epic ID ready.
