"""Tests for the CHANGELOG entry guard (CONTRIBUTING.md's per-PR requirement).

CONTRIBUTING.md line 110 requires every PR to add an entry under `## Unreleased`.
Nothing enforced it: CLAUDE.md mentions CHANGELOG only under Releasing, and the 1b
prompt's Full Cycle Scope checklist -- the list whose stated purpose is "these are not
cleanup items, name them in the plan so CHECK can verify them" -- omits it entirely.
Five substantive changes across three PRs shipped without an entry before anyone noticed.

The rule is expressed as a pure function over changed paths so it is testable without a
git repository or a live pull request.
"""

import unittest

from check_changelog import CHANGELOG, check_changelog, needs_changelog_entry


class TestNeedsChangelogEntry(unittest.TestCase):
    def test_skill_source_requires_an_entry(self):
        self.assertTrue(needs_changelog_entry(["skill/build.py"]))

    def test_phase_masters_require_an_entry(self):
        for master in (
            "1. Plan/1a Analyze to determine approach for achieving the goal.md",
            "2. Do/2. Test Drive the Change.md",
            "3. Check/3. Completeness Check.md",
            "4. Act/4. Retrospect for continuous improvement.md",
            "Human Working Agreements.md",
        ):
            with self.subTest(master=master):
                self.assertTrue(needs_changelog_entry([master]))

    def test_workflows_require_an_entry(self):
        """CI and release behavior is user-visible to contributors."""
        self.assertTrue(needs_changelog_entry([".github/workflows/release.yml"]))

    def test_readme_alone_does_not_require_an_entry(self):
        """Prose fixes are not release-note material; the rule must not cry wolf."""
        self.assertFalse(needs_changelog_entry(["README.md", "CONTRIBUTING.md"]))

    def test_changelog_alone_does_not_require_an_entry(self):
        self.assertFalse(needs_changelog_entry([CHANGELOG]))

    def test_generated_eval_results_do_not_require_an_entry(self):
        """eval/results/ is a gitignored run artifact, not a change."""
        self.assertFalse(needs_changelog_entry(["skill/eval/results/report_1.md"]))

    def test_empty_diff_does_not_require_an_entry(self):
        self.assertFalse(needs_changelog_entry([]))


class TestCheckChangelog(unittest.TestCase):
    def test_missing_entry_is_reported(self):
        problems = check_changelog(["skill/build.py"])
        self.assertTrue(problems)
        self.assertIn("CHANGELOG.md", " ".join(problems))

    def test_entry_present_passes(self):
        self.assertEqual(check_changelog(["skill/build.py", CHANGELOG]), [])

    def test_unaffected_paths_pass(self):
        self.assertEqual(check_changelog(["README.md"]), [])

    def test_problem_names_a_triggering_path(self):
        """The message must say WHICH change triggered the requirement."""
        problems = check_changelog(["skill/build.py", "docs/x.md"])
        self.assertIn("skill/build.py", " ".join(problems))


if __name__ == "__main__":
    unittest.main()
