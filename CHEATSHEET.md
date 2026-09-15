# PDCA Cheat Sheet — for the human operator

Full prompts: `skill/pdca-framework/references/` (or `1. Plan/` – `4. Act/` in this source repo).

## Nothing else knows the goal

State the goal in one sentence: *"After this session, ___."* Can't finish it, don't start —
nothing else knows what you're trying to accomplish.

## Nobody pastes the template

Natural language, not a template. Name "pdca," the phase, and what you want — the skill
expands it, you don't paste anything:

- *"use pdca to analyze what we need to do to get meaningful metrics from this repo."*
- *"per pdca plan the work in beads, look for opportunities for parallel work, use sonnet
  subagents to perform the work."*
- *"per pdca analyze, plan with beads, and spawn subagents to remedy the P1 bug."*
- *"per pdca do 0a3m"* — a specific, already-planned beads item, nothing else needed.

Name the model or subagent strategy in the same breath if you have one — "use sonnet
subagents," "spawn an opus subagent for that" — it doesn't default to anything sane on its own.

## PLAN

The architecture search before any recommendation is already mandatory in the prompt. Your
job is to check it happened — the plan should name specific files and existing patterns it
found, not gesture at "similar functionality." No evidence, no plan. Send it back.

Each step should be small enough to test alone, and land in beads if the work will outlive
this context window or run across parallel subagents. Say the standard explicitly if you want
it — real example: *"make sure the beads issue(s) have the complete details per PDCA plan and
do"* — because "complete" isn't a checkbox, it means the epic has acceptance criteria and
resumption context, and each task under it has Before / After / Done-when, not just a title.

## DO

Before you let it start — or before you hand a step to a subagent — ask: *"Have you given it
pdca do guidance?"* Guidance not loaded is guidance not followed.

- The called shot — test name, behavior, expected failure, why this test — is already
  mandatory before every test. If it starts writing one without saying this first, stop it.
- A RED that's a compile error, not a behavioral failure, is already something the prompt
  tells it to catch and diagnose. Notice when it doesn't.
- "All done" mid-DO is premature. DO ends with a handoff line. The verdict is CHECK's.

## Long sessions drift

A long session drifts. Check in against beads, not memory: *"are we on our plan or not?"*
*"what's left in the plan?"* *"there are still N open tasks."* Do this every time you resume
after a break, a context reset, or a subagent report — not just once at the start.

## The moment this is actually for

Real example, verbatim in shape: mid-investigation, before writing anything, it stopped —
*"The acceptance criteria says 'fresh clone reproduces 0.00% duplication.' That's wrong — the
actual result is 1.57%. Should I correct the acceptance criteria before committing?"* The
human's whole job at that moment was one word: *"yes."*

That's the real trade. It surfaces a finding that contradicts the plan instead of silently
fixing it or silently ignoring it; you make the call. If it never stops to ask, either nothing
has been wrong yet or it's not surfacing what it finds — the second one you won't see coming.

## CHECK

Send: *"Review our original goal outcome and plan against our execution,"* then the
checklist from `references/check-prompts.md`.

- The checklist doesn't require evidence for "tests passing" or "no untested implementation."
  You do. Don't accept either without the actual output or diff in front of you.
- When it asks which model runs the critic pass, that question is yours. Don't let it pick
  quietly.
- Read the outstanding items before the verdict. Open items and "Complete" don't coexist.

## ACT

In fast beads-driven cycles this compresses — you'll see it announce **"CHECK / ACT"** as one
step, not a separate five-stage session: what changed, what's worth noting for later, what's
next. Real example: *"Committed and closed. Two findings worth noting for future work: ...
Next: u2eq, or do you want to look at GitHub issues first?"* Your job is the same either way —
the choice of what's next, or what ONE thing changes, is yours. It proposes; you decide.

Don't mistake the compressed version for a skipped one. It's skipped when nothing gets named
for later and nothing gets asked — not when the asking is short.

## What you say when something's off

Interrupt mid-response, not after. The canonical four:
- *"You broke from test-driving. Is there adequate test coverage?"*
- *"Where's the failing test first?"*
- *"You're fixing multiple things. Focus on one failing test?"*
- *"This feels like scope creep. Are we still on step [N]?"*

In practice you'll also just say what's actually wrong, plainly: *"I don't understand what
you're saying — say it in plainer English."* *"Don't delete the data."* However you say it,
it stops and answers before continuing. Every time.

## Nothing catches this but you

- Smallest change that addresses the issue, or is it doing more than asked?
- Working inside the existing architecture, or quietly rewriting it?
- Did it read the existing test before assuming what it should do?
- Understands the component it's touching, or guessing?
- Extra caution on anything called from many places.
- A test breaks — genuinely different approach, or patching the patch?
- Can it explain why this approach, not just what it did?
- Precise, correct terminology, or hand-waving?

Can't answer one from what's on screen — ask before you approve the step.

## Off the rails

1. Stop the thread. Don't let it finish the response first.
2. Say what you're observing.
3. Repost the relevant phase prompt.
4. Redirect and resume.

## One eval run tells you nothing

A single eval run doesn't tell you a prompt edit caused a failure — scenarios fail on
unmodified text too. Interleave control/treatment, read the Fisher p-value. See `CLAUDE.md`.
