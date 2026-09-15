# PDCA Cheat Sheet — for the human operator

Full prompts: `skill/pdca-framework/references/` (or `1. Plan/` – `4. Act/` in this source repo).

## Before you start

State the goal in one sentence: *"After this session, ___."* Can't finish it, don't start —
nothing else knows what you're trying to accomplish.

## PLAN

Analysis (1a) — send: *"I need to do a high level design brainstorm. The overall goal is
to ___."* The architecture search before any recommendation is already mandatory in the
prompt. Your job: check it happened. The output should name specific files and existing
patterns it found, not gesture at "similar functionality." No evidence, no plan — send it
back.

The plan itself (1b) — once 1a is refined with questions, send: *"Based on our analysis,
provide a coherent plan incorporating our refinements..."* Each numbered step should be
small enough to test alone. Too big — say so before DO starts.

## DO

No fill-in-the-blank template — name the step and the concrete unit of work, e.g.:
*"Step 2: implement `WebhookDelivery.create(event_type:, payload:)`. Begin this step."*

- The called shot — test name, behavior, expected failure, why this test — is already
  mandatory before every test. If it starts writing one without saying this first, stop it.
- A RED that's a compile error, not a behavioral failure, is already something the prompt
  tells it to catch and diagnose. Notice when it doesn't.
- "All done" mid-DO is premature. DO ends with a handoff line. The verdict is CHECK's.

## CHECK

Send: *"Review our original goal outcome and plan against our execution,"* then the
checklist from `references/check-prompts.md`.

- The checklist doesn't require evidence for "tests passing" or "no untested implementation."
  You do. Don't accept either without the actual output or diff in front of you.
- When it asks which model runs the critic pass, that question is yours. Don't let it pick
  quietly.
- Read the outstanding items before the verdict. Open items and "Complete" don't coexist.

## ACT

Invoke it. It opens with *"Let's take a few minutes to reflect on this session,"* presents
its analysis, then asks what stood out to you — yours to answer, not to skip. Hypotheses
come from it; the choice of what changes next session is yours. One thing.

## What you say when something's off

Interrupt mid-response, not after.
- *"You broke from test-driving. Is there adequate test coverage?"*
- *"Where's the failing test first?"*
- *"You're fixing multiple things. Focus on one failing test?"*
- *"This feels like scope creep. Are we still on step [N]?"*

It stops and answers before continuing. Every time.

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

## Validating a prompt/rubric change

A single eval run doesn't tell you a prompt edit caused a failure — scenarios fail on
unmodified text too. Interleave control/treatment, read the Fisher p-value. See `CLAUDE.md`.
