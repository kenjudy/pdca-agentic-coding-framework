**Decision probe (30 sec):**

- Does this plan span 3+ files, introduce a new architectural pattern, or touch a widely-used shared abstraction? → if yes: before starting implementation, ask the operator whether they want an adversarial critic pass on this analysis and plan with a fresh subagent, as a supplement to their own review. Ask the operator which model to use (e.g. a higher-tier model than the one that produced it, or a model built for critique) rather than defaulting to one silently.
