"""Tests for the per-phase Claude Code slash commands (#188).

These are static content-shape assertions in the same spirit as test_build.py's
pinning tests for the skill's master prompts -- deterministic, no API calls, no
eval harness involved. They validate the *structure* of the command files
(existence, cross-references, phase separation); they cannot validate that a
live Claude Code session actually discovers or resolves them correctly -- that
requires a fresh interactive session and is out of reach of this test suite
(see #188's own open verification item).
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
COMMANDS_DIR = REPO_ROOT / "plugins" / "pdca-framework" / "commands"
SKILL_MD = REPO_ROOT / "skill" / "pdca-framework" / "SKILL.md"

EXPECTED_COMMAND_FILES = [
    "pdca.md",
    "pdca-plan.md",
    "pdca-do.md",
    "pdca-check.md",
    "pdca-act.md",
]

ALL_PHASE_REFERENCE_FILES = [
    "plan-prompts.md",
    "do-prompts.md",
    "check-prompts.md",
    "act-prompts.md",
]

# Each single-phase command's own reference file, and the other three commands
# it must explicitly decline to proceed into.
SINGLE_PHASE_FILES = {
    "pdca-plan.md": {"own_reference": "plan-prompts.md", "other_commands": ["/pdca-do", "/pdca-check", "/pdca-act"]},
    "pdca-do.md": {"own_reference": "do-prompts.md", "other_commands": ["/pdca-plan", "/pdca-check", "/pdca-act"]},
    "pdca-check.md": {"own_reference": "check-prompts.md", "other_commands": ["/pdca-plan", "/pdca-do", "/pdca-act"]},
    "pdca-act.md": {"own_reference": "act-prompts.md", "other_commands": ["/pdca-plan", "/pdca-do", "/pdca-check"]},
}

SECTION_HEADER_RE = re.compile(r'its "([^"]+)" section in SKILL\.md')


class TestCommandFilesExist(unittest.TestCase):
    def test_exact_file_set_exists(self):
        """The command directory must contain exactly the expected 5 files --
        not just 'at least these', so a missing or renamed file fails loudly."""
        self.assertTrue(COMMANDS_DIR.is_dir(), f"Missing commands directory: {COMMANDS_DIR}")
        actual = sorted(p.name for p in COMMANDS_DIR.glob("*.md"))
        self.assertEqual(actual, sorted(EXPECTED_COMMAND_FILES))

    def test_files_non_empty_with_frontmatter_description(self):
        for name in EXPECTED_COMMAND_FILES:
            path = COMMANDS_DIR / name
            content = path.read_text()
            self.assertGreater(len(content), 0, f"{name} is empty")
            self.assertTrue(content.startswith("---\n"), f"{name} missing YAML frontmatter")
            frontmatter = content.split("---", 2)[1]
            self.assertIn("description:", frontmatter, f"{name} frontmatter missing description:")


class TestPhaseSeparation(unittest.TestCase):
    def test_single_phase_files_reference_only_own_phase(self):
        for name, spec in SINGLE_PHASE_FILES.items():
            content = (COMMANDS_DIR / name).read_text()
            own = spec["own_reference"]
            self.assertIn(own, content, f"{name} does not reference its own {own}")
            other_references = [ref for ref in ALL_PHASE_REFERENCE_FILES if ref != own]
            for ref in other_references:
                self.assertNotIn(ref, content, f"{name} leaks a cross-phase reference to {ref}")

    def test_single_phase_files_say_do_not_proceed(self):
        for name, spec in SINGLE_PHASE_FILES.items():
            content = (COMMANDS_DIR / name).read_text()
            self.assertIn("Do not proceed", content, f"{name} missing explicit do-not-proceed instruction")
            for other_command in spec["other_commands"]:
                self.assertIn(other_command, content, f"{name} does not name {other_command} as a separate command")

    def test_full_cycle_references_all_four(self):
        content = (COMMANDS_DIR / "pdca.md").read_text()
        for ref in ALL_PHASE_REFERENCE_FILES:
            self.assertIn(ref, content, f"pdca.md does not reference {ref}")


class TestSectionHeadersMatchCurrentSkillMd(unittest.TestCase):
    """Live cross-check (not a hardcoded parallel map): extract the section header
    each command file itself quotes, then confirm that exact string is still
    present in SKILL.md today. Catches future SKILL.md section renames."""

    def test_quoted_section_headers_are_current(self):
        skill_md = SKILL_MD.read_text()
        for name in SINGLE_PHASE_FILES:
            content = (COMMANDS_DIR / name).read_text()
            match = SECTION_HEADER_RE.search(content)
            self.assertIsNotNone(match, f"{name} does not quote a SKILL.md section header in the expected form")
            header = match.group(1)
            self.assertIn(
                header, skill_md, f"{name} quotes SKILL.md section {header!r}, which is not currently present"
            )


class TestPlanCommandSequencing(unittest.TestCase):
    def test_1a_precedes_1b_and_both_are_named(self):
        content = (COMMANDS_DIR / "pdca-plan.md").read_text()
        self.assertIn("1a", content)
        self.assertIn("1b", content)
        self.assertLess(content.index("1a"), content.index("1b"), "pdca-plan.md must sequence 1a before 1b")


if __name__ == "__main__":
    unittest.main()
