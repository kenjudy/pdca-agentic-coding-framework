---

# Beads Integration (Optional)

**If beads is configured and you have an epic ID from PLAN phase**, track TDD progress:

## Before Each TDD Step

```bash
# Create subtask for this TDD iteration
bd create "Step [N]: [description]" --parent [epic-id] --type task

# Example: bd create "Step 1: Write failing test for JWT middleware" --parent PDCA-a1b2

# Claim and mark in progress
bd update [task-id] --claim --status in_progress
```

Add context so the task is self-contained:

```bash
bd update [task-id] --append-notes "$(cat <<'EOF'
Before: [current behavior or failing test name]
After: [expected behavior when this step is done]
Done when: [specific test passes or explicit verifiable condition]
EOF
)"
```

**If the feature has conditional branches**, record the test ordering decision before writing any tests:

```bash
bd update [task-id] --append-notes "$(cat <<'EOF'
TDD ordering: [conditional branch test name] before [happy-path test name]
Reason: writing the happy-path test first risks implementing the full conditional
in one GREEN step, making subsequent conditional-branch tests vacuously green.
EOF
)"
```

Why this note matters: it survives context compaction. Run `bd show [task-id]` mid-session to recover the ordering decision before writing a GREEN phase. Without this note, a long DO session can drift toward implementing all conditional logic at once, letting later tests pass before they are written.

*(Prevents ordering-triggered vacuous greens -- the multi-session form of Anti-Pattern #7. See `references/testing-anti-patterns.md` #7.)*

## After RED → GREEN → REFACTOR

```bash
# Commit the minimal change for this TDD cycle (one test, one commit)
git add [test file] [production file]
git commit -m "test: [test name] passes"
hash=$(git rev-parse --short HEAD)

# Close task with the real commit hash
bd close [task-id] --message "✓ Tests pass, committed $hash"
```

## Track Blocked Work

If a step reveals a dependency:

```bash
# Create blocker task
bd create "Blocker: [issue description]" --type bug

# Link dependency
bd dep add [current-task-id] [blocker-id]
```

**Why use beads in DO phase:**
- Each TDD cycle has discrete task with clear done criteria
- Dependency graph shows implementation sequence
- Easy to resume after interruption
- Commit hashes linked to tasks for traceability

**Review progress anytime:**

```bash
bd list --parent [epic-id]           # See all subtasks
bd list --parent [epic-id] --status in_progress  # Current work
```

---

**Next**: When all planned steps complete, proceed to CHECK phase.
