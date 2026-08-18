"""Verify a release tag agrees with README.md and CHANGELOG.md before publishing.

`tests/test_build.py::TestReadme::test_current_version_matches_changelog` ties the two
files to each other, which catches the drift that actually happened at v1.2.0 (the
release checklist's "update skill/README.md" step was skipped and nothing failed).
It cannot catch a third case: both files agreeing at one version while the release is
tagged at another. At unit-test time there is no tag to compare against.

The release workflow has one -- `github.ref_name` -- so the check lives here and runs
there, with the tag passed in. Every disagreement is reported in a single run, so a
maintainer fixes them all at once rather than discovering the next one by re-tagging.

    python3 check_release_version.py v1.3.0

Exits 0 when consistent, 1 otherwise, printing each problem to stderr.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

README_VERSION = re.compile(r"\*\*Current Version:\*\*\s*v?(\d+\.\d+\.\d+)")

# Anchored at line start and requiring "v" plus a dotted triple, so "## Unreleased" and
# prose headings like "## What Changed" cannot be mistaken for the newest release.
CHANGELOG_RELEASE = re.compile(r"^## v(\d+\.\d+\.\d+)", re.MULTILINE)


def _normalize(tag: str) -> str:
    """Drop a leading 'v' so 'v1.3.0' and '1.3.0' compare equal."""
    return tag[1:] if tag.startswith("v") else tag


def check_release_version(tag: str, repo_root: Path) -> list[str]:
    """Return every disagreement between `tag`, README.md, and CHANGELOG.md.

    An empty list means the three agree and the release is safe to publish.
    """
    version = _normalize(tag)
    problems: list[str] = []

    readme_path = repo_root / "skill" / "README.md"
    if not readme_path.is_file():
        problems.append(f"README not found at {readme_path}")
    else:
        match = README_VERSION.search(readme_path.read_text())
        if match is None:
            problems.append(
                f"{readme_path} has no '**Current Version:** vX.Y.Z' line to check against tag {tag}"
            )
        elif match.group(1) != version:
            problems.append(
                f"README says v{match.group(1)} but the release is tagged {tag} -- "
                "update skill/README.md's '**Current Version:**' line"
            )

    changelog_path = repo_root / "CHANGELOG.md"
    if not changelog_path.is_file():
        problems.append(f"CHANGELOG not found at {changelog_path}")
    else:
        match = CHANGELOG_RELEASE.search(changelog_path.read_text())
        if match is None:
            problems.append(
                f"{changelog_path} has no '## vX.Y.Z' released-version heading to check against tag {tag}"
            )
        elif match.group(1) != version:
            problems.append(
                f"CHANGELOG's newest released heading is v{match.group(1)} but the release is "
                f"tagged {tag} -- promote the '## Unreleased' section to '## v{version}' before tagging"
            )

    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0] if argv else 'check_release_version.py'} <tag>", file=sys.stderr)
        return 2

    # This file lives in skill/, so the repo root is its parent's parent.
    repo_root = Path(__file__).resolve().parent.parent
    problems = check_release_version(argv[1], repo_root)

    if problems:
        print(f"Release version check failed for tag {argv[1]}:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"Release version check passed: tag {argv[1]} agrees with README.md and CHANGELOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
