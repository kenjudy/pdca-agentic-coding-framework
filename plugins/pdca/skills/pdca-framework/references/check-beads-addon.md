---

# Beads Integration (Optional)

**If beads is configured**, validate completeness against your beads task graph:

## Review All Planned Tasks

```bash
# List all subtasks for this epic
bd list --parent [epic-id]

# Check for incomplete work
bd list --parent [epic-id] --status open,in_progress

# Review epic with full context
bd show [epic-id]
```

## Verification Checklist

**Compare beads tasks against your original plan:**

- [ ] All planned subtasks are closed
- [ ] No tasks marked `in_progress` (finish or create follow-up)
- [ ] Acceptance criteria from epic verified against actual outcomes
- [ ] Commit hashes documented in task messages
- [ ] Any discovered blockers have follow-up tasks created

**If discrepancies found:**
- Open tasks that weren't in original plan? → Reassess scope
- Planned tasks not in beads? → Create them or document why skipped
- In-progress tasks? → Complete or explicitly defer with reason

**Why use beads in CHECK phase:**
- Objective completeness verification (task graph vs. subjective memory)
- Ensures no half-finished work left behind
- Documents any scope changes discovered during implementation

---

**If CHECK passes**, proceed to ACT phase for retrospection.

**If CHECK fails**, return to DO phase to complete remaining work.
