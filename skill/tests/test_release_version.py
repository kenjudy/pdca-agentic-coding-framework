"""Tests for the release version-consistency check (issue #89 follow-on, release guard).

`tests/test_build.py::TestReadme::test_current_version_matches_changelog` ties
README.md's "Current Version" to CHANGELOG.md's newest released heading. It cannot
see the git tag, because at unit-test time there isn't one -- so both files can agree
at v1.2.0 while the release is tagged v1.3.0, and the suite stays green while a
mislabeled package is published.

`check_release_version.py` closes that: the release workflow passes it the tag it is
building, and it reports every disagreement between the tag, README, and CHANGELOG.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from check_release_version import check_release_version

CHANGELOG_TEMPLATE = """# Changelog

## Unreleased

- something not yet released

## v{released} (2026-07-17)

- the previous release

## v1.1.0 (2026-05-28)

- older still

## What Changed

- a non-version heading that must not be mistaken for a release
"""

README_TEMPLATE = """# Skill

Some prose.

## Version Information

**Current Version:** v{readme}

More prose.
"""

PLUGIN_JSON_TEMPLATE = """{{
  "name": "pdca",
  "version": "{plugin}",
  "description": "TDD-disciplined AI code generation using Plan-Do-Check-Act methodology.",
  "author": {{"name": "Ken Judy", "email": "ken@kenjudy.us"}}
}}
"""


def _repo(readme: str, released: str, plugin: str | None = None) -> TemporaryDirectory:
    """Build a throwaway repo root with a README, CHANGELOG, and plugin.json at the
    given versions. `plugin` defaults to `released` so existing callers that don't
    care about plugin.json get a value that never contributes an extra problem."""
    if plugin is None:
        plugin = released
    tmp = TemporaryDirectory()
    root = Path(tmp.name)
    (root / "skill").mkdir()
    (root / "skill" / "README.md").write_text(README_TEMPLATE.format(readme=readme))
    (root / "CHANGELOG.md").write_text(CHANGELOG_TEMPLATE.format(released=released))
    plugin_dir = root / "plugins" / "pdca" / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(PLUGIN_JSON_TEMPLATE.format(plugin=plugin))
    return tmp


class TestReleaseVersionCheck(unittest.TestCase):
    def test_accepts_tag_matching_both_files(self):
        with _repo(readme="1.2.0", released="1.2.0") as root:
            self.assertEqual(check_release_version("v1.2.0", Path(root)), [])

    def test_accepts_tag_without_v_prefix(self):
        """The tag is the source of truth for its own spelling; 'v' is optional."""
        with _repo(readme="1.2.0", released="1.2.0") as root:
            self.assertEqual(check_release_version("1.2.0", Path(root)), [])

    def test_rejects_tag_ahead_of_both_files(self):
        """The hole the README<->CHANGELOG test cannot see: both agree, tag does not.

        Publishing here would attach a package whose README says v1.2.0 to a release
        labeled v1.3.0, with every existing test green.
        """
        with _repo(readme="1.2.0", released="1.2.0") as root:
            problems = check_release_version("v1.3.0", Path(root))

        self.assertTrue(problems, "a tag matching neither file must be reported")
        joined = " ".join(problems)
        self.assertIn("1.3.0", joined)
        self.assertIn("1.2.0", joined)

    def test_rejects_stale_readme(self):
        with _repo(readme="1.2.0", released="1.3.0") as root:
            problems = check_release_version("v1.3.0", Path(root))

        self.assertTrue(problems, "a README behind the tag must be reported")
        self.assertIn("README", " ".join(problems))

    def test_rejects_changelog_without_the_release(self):
        with _repo(readme="1.3.0", released="1.2.0") as root:
            problems = check_release_version("v1.3.0", Path(root))

        self.assertTrue(problems, "a CHANGELOG lacking the tagged release must be reported")
        self.assertIn("CHANGELOG", " ".join(problems))

    def test_reports_both_problems_at_once(self):
        """A maintainer should learn about every mismatch in one run, not one per re-tag."""
        with _repo(readme="1.1.0", released="1.2.0", plugin="1.3.0") as root:
            problems = check_release_version("v1.3.0", Path(root))

        self.assertEqual(len(problems), 2, f"expected a README and a CHANGELOG problem, got: {problems}")

    def test_rejects_stale_plugin_json(self):
        """#203: plugin.json now gates marketplace delivery -- if it's behind the
        tag, installed users silently never receive the release, unlike a stale
        README, which is merely inaccurate."""
        with _repo(readme="1.3.0", released="1.3.0", plugin="1.1.0") as root:
            problems = check_release_version("v1.3.0", Path(root))

        self.assertTrue(problems, "a plugin.json behind the tag must be reported")
        self.assertIn("plugin.json", " ".join(problems))

    def test_reports_missing_readme_version_line(self):
        with TemporaryDirectory() as name:
            root = Path(name)
            (root / "skill").mkdir()
            (root / "skill" / "README.md").write_text("# Skill\n\nNo version line here.\n")
            (root / "CHANGELOG.md").write_text(CHANGELOG_TEMPLATE.format(released="1.3.0"))
            problems = check_release_version("v1.3.0", root)

        self.assertTrue(problems)
        self.assertIn("Current Version", " ".join(problems))

    def test_ignores_unreleased_and_non_version_headings(self):
        """'## Unreleased' and '## What Changed' must not be read as the newest release."""
        with _repo(readme="1.2.0", released="1.2.0") as root:
            self.assertEqual(check_release_version("v1.2.0", Path(root)), [])


if __name__ == "__main__":
    unittest.main()
