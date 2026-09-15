# PDCA Cheat Sheet — for the human operator

This is about what *you* do each session, not what the agent produces. Full prompts live in
`skill/pdca-framework/references/` (or `1. Plan/` – `4. Act/` in this source repo).

## Open every session by saying this

1. State the goal in one sentence: *"After this session, ___."* If you can't finish that sentence,
   don't start — you won't be able to tell CHECK or ACT whether you succeeded.
2. Tell the agent, out loud, before it writes anything: **TDD, no exceptions. One failing test at a
   time. Work within existing architecture. Ask before a big or ambiguous change.** Don't assume it
   remembers this from the system prompt — say it.
3. Decide your intervention rights now: you will stop the agent mid-response when you see a
   violation. Agreeing to that up front is what makes doing it later not feel rude.

## Your job, phase by phase

**1. PLAN** — Don't accept a plan built on no evidence. Ask: *"What did you find when you searched
for how this is already done here?"* If the answer is vague or absent, send it back. Read the
numbered steps — each one should be small enough to test in isolation. If a step looks too big,
say so before DO starts, not after.

**2. DO** — This is where you stay in the loop, not where you go get coffee.
- Before *every* test, the agent must tell you: what it's named, what behavior it verifies, what
  failure it expects, and why this test next. If it starts writing a test (or code) without saying
  this first, **stop it right there.**
- When it says a test is RED, glance at *why*. A compile error is not RED. Make it confirm the
  failure is the right one.
- One test, one fix, at a time. The moment it's touching things unrelated to the current test,
  stop it.
- If it declares the work done mid-DO ("all done," "that's everything"), that's premature — DO ends
  with a handoff line, not a verdict. The verdict is CHECK's job, not DO's.

**3. CHECK** — Your job here is to *not* rubber-stamp. A green build is necessary, not sufficient.
- Don't accept "all tests passing" without asking to see the output.
- Don't accept "no untested implementation" without asking for the diff of implementation vs. test
  files.
- Read the outstanding items list before you read the verdict. If items are open, "Complete" is the
  wrong answer regardless of how confident the summary sounds.

**4. ACT** — Answer the open question yourself; don't let the agent interpret its own session for
you. When it offers hypotheses, you decide which one lands, and you pick the ONE thing to change
next time — not it.

## The four questions you ask when something's off

Interrupt immediately. Don't let a violation ride to the end of the response.
- *"You broke from test-driving. Is there adequate test coverage?"*
- *"Where's the failing test first?"*
- *"You're fixing multiple things. Focus on one failing test?"*
- *"This feels like scope creep. Are we still on step [N]?"*

The agent must stop and answer before continuing. Process discipline beats immediate progress —
every time, not just when convenient.

## What you're watching for, across the whole session

- Is the change the smallest one that addresses the issue, or is it doing more than asked?
- Is it working within the architecture that's already there, or quietly rewriting it?
- Did it read the existing test before assuming what it should do?
- Does it understand a component before touching it, or is it guessing?
- Extra caution on anything called from many places — one change there ripples.
- When a test breaks, is it trying a genuinely different approach, or patching the patch?
- Can it explain *why* this approach, not just *what* it did?
- Is it using precise, correct terminology for this domain, or hand-waving?

If you can't answer one of these from what's on screen, ask before you approve the step.

## When it goes off the rails

1. Stop the thread immediately — don't let it finish the response first.
2. Say plainly what you're observing.
3. Repost the relevant phase prompt.
4. Redirect and resume.

## Validating a prompt/rubric change

Never trust a single eval run — scenarios fail on unmodified text too. Always interleave
control/treatment and read the Fisher p-value, never two raw pass rates. See `CLAUDE.md`.
