# Independent CHECK Agent — Learnings

**Source session:** agentic-pdlc IFPUG function point estimation, September 2026
**See also:** [[Autonomous Subagent DO Phase - Learnings]]

---

## What happened

The CHECK phase used a Fable fork seeded only with the spec (PDCA analysis) and the implementation outputs -- not the conversation that produced them. It found 10 issues: 0 critical, 3 major, 4 minor, 3 pass. All 3 major issues were real bugs:

- `eif_delta.pass2_dets` always showed the pass-3 value (both sides of the delta used `currentDets`)
- `contract-design` frontmatter said `mob-parallel` but step 4 required sequential execution
- Empty catalog returned `High` confidence instead of a sentinel `Low`

These were correctness bugs invisible to the agents that built the feature, because those agents had the context of their own decisions and never questioned the invariants they had established.

---

## The independence principle

The value of the CHECK agent is directly proportional to its independence from the DO phase. An agent that participated in building the feature has anchoring bias toward its own decisions. It will verify that the code does what the agent intended, not whether the intent was correct.

**Use a model with no prior involvement.** Fable (or a fresh Opus instance in a new session) has no memory of the DO-phase reasoning. It reads the spec and the output and asks: do these match? That's the question the DO agents cannot reliably ask about their own work.

**Seed it narrowly.** Give the CHECK agent the spec (the analysis or requirements), the implementation outputs, and nothing else. Giving it the conversation that produced the outputs contaminates its independence -- it will understand and rationalize the same decisions the DO agents made.

---

## What to watch for

A CHECK agent that returns only minor style findings and no substantive issues is a signal, not a result. Either the implementation is genuinely clean, or the agent is reasoning from the same frame as the DO agents. If the CHECK agent had access to the DO-phase conversation, suspect the latter.

The Fable fork in this session initially returned a status message rather than findings. When it did return findings, they were substantive. The gap between first return and actual findings is worth noting: always verify the result is real output before treating the CHECK phase as complete.
