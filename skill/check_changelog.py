"""Require a CHANGELOG entry on pull requests that change behavior.

CONTRIBUTING.md requires every PR to add an entry under `## Unreleased`. Nothing
enforced it, and it was routinely missed: CLAUDE.md mentions CHANGELOG only under
Releasing (reading as a release-time task), and the 1b prompt's Full Cycle Scope
checklist -- whose stated purpose is "these are not cleanup items, name them in the
plan so CHECK can verify them like any other step" -- omits it entirely. Five
substantive changes across three PRs shipped without an entry before it was noticed.

This is deliberately a PR-scoped check rather than a unit test. A unit test cannot see
a diff, so the most it could assert is that `## Unreleased` exists and is non-empty --
which passes forever once any single entry is added, and would never catch the PR that
forgot. The information needed lives only in the pull request, so the guard runs there.

    python3 check_changelog.py <base-ref>

Exits 0 when satisfied, 1 otherwise, printing each problem to stderr.
"""

from __future__ import annotations

import subprocess
import sys

CHANGELOG = "CHANGELOG.md"

# Paths whose change is release-note material. Prose-only files (README, CONTRIBUTING,
# AGENTS) are deliberately absent: a guard that fires on a typo fix trains people to
# work around it, and a guard people route around protects nothing.
REQUIRES_ENTRY = (
    "skill/",
    "1. Plan/",
    "2. Do/",
    "3. Check/",
    "4. Act/",
    "Human Working Agreements.md",
    ".github/workflows/",
)

# Generated run artifacts, gitignored. Their presence in a diff is not a change.
EXEMPT = ("skill/eval/results/",)


def needs_changelog_entry(changed_paths: list[str]) -> bool:
    """True when any changed path is release-note material."""
    return any(_triggering(changed_paths))


def _triggering(changed_paths: list[str]) -> list[str]:
    return [
        path
        for path in changed_paths
        if path != CHANGELOG
        and not path.startswith(EXEMPT)
        and path.startswith(REQUIRES_ENTRY)
    ]


def check_changelog(changed_paths: list[str]) -> list[str]:
    """Return problems; empty means the diff satisfies CONTRIBUTING.md's rule."""
    triggering = _triggering(changed_paths)
    if not triggering:
        return []
    if CHANGELOG in changed_paths:
        return []

    shown = ", ".join(sorted(triggering)[:3])
    more = f" (and {len(triggering) - 3} more)" if len(triggering) > 3 else ""
    return [
        f"This pull request changes {shown}{more} but does not touch {CHANGELOG}. "
        "CONTRIBUTING.md requires an entry under an '## Unreleased' section, grouped "
        "under a '### Category' subheading. If the change requires action from existing "
        "users, add a '### Migration Notes' subsection. Running `/update-changelog` in "
        "Claude Code drafts entries from your commits."
    ]


def _changed_paths(base_ref: str) -> list[str]:
    """Paths differing between the merge base and HEAD."""
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in diff.stdout.splitlines() if line]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0] if argv else 'check_changelog.py'} <base-ref>", file=sys.stderr)
        return 2

    try:
        paths = _changed_paths(argv[1])
    except subprocess.CalledProcessError as error:
        print(f"Could not diff against {argv[1]}: {error.stderr.strip()}", file=sys.stderr)
        return 2

    problems = check_changelog(paths)
    if problems:
        print("CHANGELOG check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"CHANGELOG check passed ({len(paths)} path(s) changed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
