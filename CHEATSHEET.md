# PDCA Cheat Sheet — for the human operator

Full prompts: `skill/pdca-framework/references/` (or `1. Plan/` – `4. Act/` in this source repo).

## Before PLAN starts

- State the goal in one sentence: *"After this session, ___."* Can't finish it, don't start.
- Say out loud what you expect: TDD, no exceptions. One thing at a time. Work inside the
  existing architecture. No phase prompt is loaded yet — nothing else is holding this line.
- Decide now: you will stop the agent mid-response on a violation. Not after it finishes. Mid.

## PLAN

The architecture search before any recommendation is already mandatory in the prompt. Your
job is to check it happened — the plan should name specific files and existing patterns it
found, not gesture at "similar functionality." No evidence, no plan. Send it back.

Each numbered step should be small enough to test alone. Too big — say so before DO starts.

## DO

- The called shot — test name, behavior, expected failure, why this test — is already
  mandatory before every test. If it starts writing one without saying this first, stop it.
- A RED that's a compile error, not a behavioral failure, is already something the prompt
  tells it to catch and diagnose. Notice when it doesn't.
- "All done" mid-DO is premature. DO ends with a handoff line. The verdict is CHECK's.

## CHECK

- The checklist doesn't require evidence for "tests passing" or "no untested implementation."
  You do. Don't accept either without the actual output or diff in front of you.
- When it asks which model runs the critic pass, that question is yours. Don't let it pick
  quietly.
- Read the outstanding items before the verdict. Open items and "Complete" don't coexist.

## ACT

The open question is yours to answer, not the agent's to answer for you. Hypotheses come from
it; the choice is yours. One thing.

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
