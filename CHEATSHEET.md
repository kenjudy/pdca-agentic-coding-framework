# PDCA Cheat Sheet — for the human operator

Full prompts: `skill/pdca-framework/references/` (or `1. Plan/` – `4. Act/` in this source repo).

## Using the skill

1. Aside from calling out PDCA to invoke the skill, use natural language.
2. You can invite the agent to use subagents if you run in a more autonomous mode. Name the
   model or subagent strategy in the same prompt if you have one — "use sonnet subagents,"
   "spawn an opus subagent for that."

## State a user-focused goal

Not "refactor the auth module" — "so a user can reset their password without emailing
support." What value does this work create for someone? State it in one sentence: *"After
this session, ___."* Can't finish it, don't start — nothing else knows what you're trying to
accomplish.

## PLAN

- *"use pdca to analyze what we need to do to get meaningful metrics from this repo."*

  The architecture search before any recommendation is already mandatory in the prompt. Your
  job is to check it happened — the plan should name specific files and existing patterns it
  found, not gesture at "similar functionality." No evidence, no plan. Send it back.

- *"per pdca plan the work in beads, look for opportunities for parallel work, use sonnet
  subagents to perform the work."*

  Planning itself isn't delegated — "perform the work" means the DO steps that come out of
  this plan, decided here so parallel execution is already set up before DO starts. Each step
  should be small enough to test alone, and land in beads if the work will outlive this
  context window or run across parallel subagents.

- *"make sure the beads issue(s) have the complete details per PDCA plan and do"*

  A separate, explicit instruction — say it if you want it enforced.
  "Complete" isn't a checkbox: the epic needs acceptance criteria and resumption context, and
  each task under it needs Before / After / Done-when, not just a title.

## DO

- *"per pdca do 0a3m"* — a specific, already-planned beads item. Nothing else needed; the
  detail lives in the plan.

Before you let it start — or before you hand a step to a subagent — ask: *"Have you given it
pdca do guidance?"*

- The called shot — test name, behavior, expected failure, why this test — is already
  mandatory before every test. If it starts writing one without saying this first, stop it.
- A RED that's a compile error, not a behavioral failure, is already something the prompt
  tells it to catch and diagnose. Notice when it doesn't.
- "All done" mid-DO is premature. DO ends with a handoff line. The verdict is CHECK's.

## Long sessions drift

A long or resumed session drifts from what you actually agreed to. Check beads, not memory:
*"are we on our plan or not?"* *"what's left in the plan?"* *"there are still N open tasks."*
Ask every time you resume — after a break, a context reset, a subagent report.

## When it finds something wrong

Mid-investigation, before writing anything, it stopped: *"The acceptance criteria says
'fresh clone reproduces 0.00% duplication.' That's wrong — the actual result is 1.57%.
Should I correct the acceptance criteria before committing?"* The human's answer was one
word: *"yes."*

It surfaced a wrong finding instead of quietly fixing it or ignoring it. You decide.

## CHECK

If it isn't prompting you into CHECK on its own, invoke it explicitly — don't wait on it.
Send *"Review our original goal outcome and plan against our execution,"* then the checklist
from `references/check-prompts.md`.

- Checking the box for "tests passing" or "no untested implementation" doesn't mean you've
  seen either. Don't accept either without the actual output or diff in front of you.
- When it asks which model runs the critic pass, that question is yours. Don't let it pick
  quietly.
- Read the outstanding items before the verdict. Open items and "Complete" don't coexist.

A "Complete" verdict it wrote itself is not your approval. Nothing closes — no issue, no
commit — until you say so explicitly. The one exception is running fully autonomous, with
nobody there to approve.

## ACT

Answer the open question yourself — don't let it interpret the session for you. Hypotheses
come from it; the choice of what changes next session is yours. One thing.

In a fast beads cycle this takes a compressed shape — you'll see it announce **"CHECK / ACT"**
as one step: *"Committed and closed. Two findings worth noting for future work: ... Next:
u2eq, or do you want to look at GitHub issues first?"* That's not proof you approved the
close — check separately whether you actually signed off.

Unless you're running fully autonomous, work isn't done when tests pass. It's done when
you've signed off on both CHECK and ACT.

## What you say when something's off

Interrupt mid-response, not after. From `Human Working Agreements.md`:
- *"You broke from test-driving. Is there adequate test coverage?"*
- *"Where's the failing test first?"*
- *"You're fixing multiple things. Focus on one failing test?"*
- *"This feels like scope creep. Are we still on step [N]?"*
- *"Which assertion did you predict, and which one fired?"*

In practice you'll also just say what's actually wrong, plainly: *"I don't understand what
you're saying — say it in plainer English."* *"Don't delete the data."* However you say it,
it stops and answers before continuing. Every time.

## What only you check

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

## Validating a prompt or rubric change

A single eval run doesn't tell you a prompt edit caused a failure — scenarios fail on
unmodified text too. Interleave control/treatment, read the Fisher p-value. See `CLAUDE.md`.
