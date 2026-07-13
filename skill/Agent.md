# Agent Instructions

This project uses **bd** (beads) for issue tracking and a **Human-Supervised PDCA cycle** for all code generation. These two systems work together. Beads tracks _what_ needs doing across sessions. The PDCA cycle governs _how_ you do it.

**You do not operate autonomously.** The human is present, reviewing, directing, and approving throughout each session. Do not push, commit, or close issues without explicit human approval.

---

## Human Supervision Protocol (Non-Negotiable)

These rules take precedence over all other instructions in this file:

- **STOP and present to the human** before writing any code
- **STOP and present to the human** before committing
- **STOP and present to the human** before pushing
- **STOP and present to the human** before closing any issue
- **STOP and present to the human** if you are about to deviate from the current plan
- When in doubt, pause and ask. Do not resolve ambiguity by proceeding.

If the human is not responding, stop work. Do not continue unattended.

---

## Session Startup

```bash
bd onboard          # Get oriented on first use
bd ready            # Show available work with no open blockers
bd show <id>        # Review issue details before starting
```

**Before any implementation begins**, complete the PDCA Plan phase:

1. Run the Analysis prompt (1a) for the selected issue
2. Run the Planning prompt (1b) to produce an atomic step plan
3. Present the plan to the human for approval
4. **Wait for explicit approval before proceeding to implementation**

Do not claim an issue (`--status in_progress`) until the human has approved the plan.

---

## During Implementation (PDCA Do Phase)

```bash
bd show <id>        # Reference the issue for acceptance criteria
bd dep add <child> <parent>   # Link related issues if discovered
```

**At each implementation step:**

- Follow TDD discipline: failing test first, no exceptions
- Present your reasoning before making changes, particularly deviations from plan
- After each step, summarize outcome and wait for human approval before proceeding
- Do not batch multiple steps without human confirmation between them

**If you observe yourself:**

- Making changes without a failing test first → Stop. Report to human.
- Modifying more files than the current step requires → Stop. Report to human.
- Losing track of the current plan step → Stop. Ask human to reorient.

---

## Session Completion (PDCA Check + Act Phases)

Work is not complete when code compiles or tests pass. Work is complete when the human has signed off on both the Check and Act phases.

**MANDATORY SEQUENCE — human approval required at each step:**

1. **Run Completeness Check** (prompt 3) — present results to human, wait for approval
2. **Run Retrospective** (prompt 4) — present insights, wait for human to determine follow-on actions
3. **File follow-up issues** — create beads issues for outstanding items identified in Check/Act
4. **Human approves commit** — you prepare the commit message, human confirms before commit
5. **Human approves push** — after commit, present to human for push authorization

```bash
bd create "Title" -p <priority>   # File follow-up issues from Check/Act
bd close <id>                     # Only after human confirms completion
bd sync                           # After human-approved push
```

**Never:**

- Say the session is complete before retrospection is done
- Close issues before the human confirms the Completeness Check
- Push without explicit human instruction to do so
- File issues on behalf of the human without discussing them first

---

## Cross-Session Continuity

Beads is the authoritative record of plan state between sessions. The conversation thread is not.

When starting a new session on a continuing story:

```bash
bd ready                          # What is actually unblocked
bd show <id>                      # What was the last state of this work
```

Reference prior issue history in your Analysis phase (1a) before re-deriving architectural decisions that may have already been made. Prior closed issues are a record of _why_ decisions were made, not just what code exists.

---

## Quick Reference

```bash
bd ready                          # Find available work
bd show <id>                      # View issue details
bd create "Title" -p <priority>   # Create follow-up issue
bd dep add <child> <parent>       # Link dependency
bd update <id> --status in_progress  # Mark in progress (after human plan approval)
bd close <id>                     # Complete (after human sign-off)
bd sync                           # Sync after human-approved push
```

---

## Working Agreements (Human Commitments)

The human operator commits to:

- Defining a clearly scoped objective before each session
- Reviewing and approving the plan before implementation begins
- Following the agent's progress and intervening when TDD discipline breaks
- Approving each commit and push explicitly
- Completing the Retrospective even when time-pressured

The agent cannot enforce these. They are the human's accountability.

---

## Validating Changes to Source Instructions

Any change to master prompt files (`1. Plan/`, `2. Do/`, etc.) or eval rubrics must follow this sequence. Do not commit without completing it.

### 1. Establish a Baseline

Check the most recent eval report:

```bash
ls -t skill/eval/results/
```

If a recent report exists, use its per-scenario scores as the baseline. If not, or if the codebase has diverged, run the full eval first:

```bash
cd skill && bash run-evals.sh
```

### 2. Make Small, Discrete Changes

- Change **one concern at a time** — a single prompt section, a single rubric criterion
- Rebuild after each change: `bash skill/build-skill.sh`
- Confirm the change appears in the built references before running evals

### 3. Re-run Evals for Affected Phases Only

Identify which phases are affected:

| Changed file | Affected eval classes |
|---|---|
| `1. Plan/1a...md` | `TestPrompt1aEvals`, `TestPrompt1bEvals` (both use `plan-prompts.md`) |
| `1. Plan/1b...md` | `TestPrompt1bEvals` |
| `2. Do/2...md` | `TestPrompt2Evals` |
| `3. Check/3...md` | `TestPrompt3Evals` |
| `4. Act/4...md` | `TestPrompt4Evals` |
| `eval/rubrics/rubric_Xb.py` | that phase's class only |

```bash
cd skill && bash run-evals.sh -k "TestPrompt1aEvals or TestPrompt1bEvals"
```

### 4. Accept Only Same-or-Better Scores

- All previously passing scenarios must still pass
- If a scenario flips from pass to fail:
  1. Check whether the failure is caused by your change or pre-existing rubric variance
  2. Re-run the scenario 1–3 times — LLM-judge scores vary naturally
  3. If the rubric is misapplying a criterion, fix the rubric (targeted change only) and re-run
- Do not commit prompt or rubric changes that regress a passing scenario

---

## Validating Trigger Accuracy

The process compliance evals above test what the skill *does* once invoked. Trigger accuracy tests whether Claude invokes the skill at the right moments. These are separate concerns and use a separate tool.

**Trigger accuracy is validated via the `skill-creator` skill**, not this test suite. The scenario inputs live in `eval/trigger-eval.json` (35 entries: 20 should-trigger, 15 should-not-trigger).

### Running a trigger accuracy check

From a new Claude Code session:

```
/skill-creator
```

Then ask it to run trigger optimization on the pdca-framework skill using `eval/trigger-eval.json` as the scenario input. Results are written to `eval/trigger-optimization-report.json`.

### Interpreting results

The report shows precision and recall across iterations:

- **Recall = 0%** on should-trigger cases means the skill description is not broad enough. The skill never fires on realistic session-start prompts. This was the finding from the April 2026 run -- all 5 description variants failed to trigger on positive cases.
- **Low precision** (false triggers) means the description is too broad and fires on unrelated requests.

### When to re-run

Re-run trigger accuracy after any change to:
- `skill/pdca-framework/SKILL.md` (the description field specifically)
- `eval/trigger-eval.json` (scenario quality improvements)

The current scenario set includes ambiguous should-trigger cases (complex features, reliability problems, messy codebases) alongside obvious ones, to prevent the optimizer from overfitting to explicit PDCA/TDD keyword mentions.
