**Decision probe (30 sec):**

- Did the implementation reveal anything the plan did not anticipate — new dependencies, structural issues, or scope changes? → if yes: flag the specific finding for the ACT retrospective before closing
- Does the changed code touch auth, data persistence, or external APIs? → if yes: run `/security-review` before committing
