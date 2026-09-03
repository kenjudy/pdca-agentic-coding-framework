# Autonomous Subagent DO Phase — Learnings

**Source session:** agentic-pdlc IFPUG function point estimation, September 2026
**Scope:** Full autonomous DO phase dispatching haiku, sonnet, and Fable subagents across 18 commits

---

## Context

This session ran the DO phase largely autonomously: the user approved the PDCA analysis and plan, then instructed the coordinator to proceed through implementation using subagents as needed. Haiku agents handled simpler stage definition updates in parallel; sonnet handled core tool implementation (fp-calc.ts, state-schema, orchestrate); a Fable fork ran the CHECK phase independently. The session spanned two context windows with a compaction boundary mid-DO.

---

## What worked well

### Stub-first TDD gate enforces clean agent contracts

Writing compilable stubs before dispatching implementation agents meant all tests failed behaviorally (on assertion), not on compilation. Each agent's job was narrowly defined: make these specific assertion messages go green. This prevented agents from drifting into architecture decisions during implementation.

The predicted-failure discipline (state the exact assertion message before running the test) caught one case where the test was actually testing the wrong thing before any implementation was written.

### Fork subagents keep parent context clean

Using fork subagents for parallel stage work meant raw tool output from those agents never appeared in the parent context. The parent only saw completion notifications and acted on them. This kept the session manageable across 100+ tool calls and through the compaction boundary.

Reserve fork subagents for work where the parent doesn't need the intermediate output -- research, parallel file updates, independent stage work. Don't fork when the result needs to be reasoned about inline.

### Analysis-before-plan surfaces design decisions early

Running the full PDCA analysis (four revisions, Fable review) before any code surfaced decisions that would have been painful to retrofit mid-DO: counting scope, the two-matrix IFPUG requirement, fp-catalog.json merge semantics, owning_context as the join key. These were spec decisions, not implementation decisions -- and they belonged in the analysis, not discovered by agents during the build.

---

## What to improve

### Concurrent agent commits cause git ref lock collisions

When multiple subagents staged their changes simultaneously and then attempted to commit, git ref lock errors occurred. In this session, the state-schema agent's commit accidentally swept up files staged by two haiku agents -- the result was correct but by accident. In a different ordering it would have silently dropped those changes.

**Pattern to adopt:** agents stage only; one coordinator commits. Or agents commit strictly sequentially with an explicit handoff. Never dispatch multiple agents that each end with a `git commit` in the same turn.

### Fork result validation before treating as complete

A Fable fork returned a status message ("The Fable CHECK fork is still running") as its result text on first return, not actual findings. The parent treated this as a complete result, which would have ended the CHECK phase with no findings. Resuming via SendMessage recovered the actual output.

**Pattern to adopt:** always inspect whether a fork result is substantive before acting on it. If the result text looks like a status message rather than the expected output format, resume the fork. A one-line check ("does this look like findings or a status update?") prevents a silent no-op CHECK.

### Subagent prompts need explicit file lists, not open-ended reads

Agents given open-ended read permission ("read what's relevant") drifted toward files that were immediately obvious rather than architecturally necessary. Agents given explicit lists ("read these three files, produce this artifact, write to this path") produced more focused, correct output in fewer tool calls.

**Pattern to adopt:** every subagent prompt should include:
- A named list of files to read (not "read what you need")
- The exact output path to write
- The schema or structure expected in the output

### Multi-agent file convergence requires explicit write-ownership

Whenever multiple agents produce outputs that converge into one file, agents will overwrite each other's fields without an explicit merge contract. In this session, fp-catalog.json was written by three different agents across three passes. The merge semantics (read existing file, update only your fields, write merged JSON back) had to be spelled out in each stage definition and in the shared knowledge file.

**Pattern to adopt:** any time a shared output file has multiple writers, the relevant stage definitions must include a write-ownership table specifying which agent writes which fields and in what order. Do not leave this implicit.

---

## Conditions where autonomous DO works well

- The analysis phase resolved all significant design decisions before implementation began
- Each agent's output is a discrete file (not a shared mutable file with multiple writers)
- Agents commit sequentially or stage-only with a single coordinator commit
- The CHECK phase uses a model with no prior involvement in the DO work

## Conditions that require closer human oversight

- Multiple agents writing to the same output file (explicit merge contract required first)
- Agents that each end with a git commit in the same parallel dispatch
- Any fork whose result format is not immediately distinguishable from a status message
- Stages where the agent needs to make architectural decisions not resolved in the plan
