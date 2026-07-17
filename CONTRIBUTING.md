# Contributing to PDCA Framework

Thank you for your interest in contributing. This project uses a
human-supervised PDCA (Plan–Do–Check–Act) cycle for all code generation,
and we ask that contributions follow the same discipline.

## Contents

- [Development Setup](#development-setup)
- [AI-Assisted Contributions](#ai-assisted-contributions)
- [Filing Issues](#filing-issues)
- [Contribution Process](#contribution-process)
- [Commit Style](#commit-style)
- [Changing Master Prompt Files](#changing-master-prompt-files)
- [Pull Requests](#pull-requests)
- [License](#license)

---

## Development Setup

```sh
cd claude-skill
uv sync            # install dependencies
bash run-tests.sh  # build skill, run ruff + mypy + pytest
```

Eval tests require an `ANTHROPIC_API_KEY` and cost ~$2–5 per run:

```sh
uv sync --extra eval
bash run-evals.sh
```

See `claude-skill/README.md` for full details.

## AI-Assisted Contributions

All changes that can be test-driven must be, regardless of whether the
implementer is human or AI. A human must be present and approving at
each PDCA gate. The human supervision protocol in `Agent.md` applies to
all code contributions.

For changes to the skill's code or prompts, we recommend using the
pdca-framework skill itself to guide your session — we use it to build
itself. Documentation changes don't require it.

## Filing Issues

Open a GitHub issue before starting any non-trivial change. Describe what
you want to fix or add and, if you have one, your proposed approach. Wait
for a response before writing code — this prevents duplicate work and lets
the maintainer flag any design concerns early.

Bug reports and feature requests without a corresponding PR are also
welcome. If you are not sure whether something is worth pursuing, open an
issue and ask.

## Contribution Process

All contributions follow the PDCA cycle:

1. **Plan** — open an issue (see above); describe the problem and your
   proposed approach. Wait for feedback before proceeding.
2. **Do** — implement using TDD: write a failing test first, and then make
   it pass. One failing test at a time, no exceptions.
3. **Check** — run the full test suite (`bash run-tests.sh`). For
   changes to master prompt files, run the affected eval classes and
   confirm that no previously-passing scenarios regress (see below).
4. **Act** — open a PR with a summary of what changed and why.

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```txt
feat: add X
fix: correct Y
docs: update Z
refactor: rename W
chore: bump dependency
```

- Subject line ≤ 50 characters. Imperative mood. No period at the end.
- Scope tags (e.g., `feat(scope):`) are optional.

## Changing Master Prompt Files

Changes to `1. Plan/`, `2. Do/`, `3. Check/`, or `4. Act/` require eval
validation before the PR can merge:

1. Record baseline scores from the most recent report in
   `claude-skill/eval/results/`.
2. Make one discrete change; rebuild: `bash claude-skill/build-skill.sh`.
3. Run only the affected eval class:

   ```sh
   cd claude-skill && bash run-evals.sh tests/test_evals.py::TestPrompt2Evals
   ```

   See `Agent.md` for the full phase → eval class mapping.

4. All previously passing scenarios must still pass. Do not submit a PR
   that regresses a passing scenario.

## Pull Requests

- Keep PRs focused on a single concern.
- Include the test(s) that cover your change in the same commit.
- Add an entry to `CHANGELOG.md` (repo root) under an `## Unreleased`
  section. Group entries under a `### Category` subheading (e.g.,
  `### New Features`, `### Bug Fixes`, `### Build and Distribution`).
  If you are using Claude Code, run `/update-changelog` to draft entries
  from your commits and write them to the file automatically.
  If your change requires any action from existing users (renamed files,
  changed install paths, removed options), add a `### Migration Notes`
  subsection.
- Reference the issue your PR addresses.

Version numbers are assigned by the maintainer at release time. Do not
bump the version in `claude-skill/README.md` yourself unless you are
cutting a release.

Dependency bump PRs are handled automatically by Dependabot. No manual
contribution needed.

## License

By contributing, you agree that your work will be released under the
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
license that covers this project.
