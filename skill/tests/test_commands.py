"""Tests for the per-phase Claude Code slash commands (#188).

These are static content-shape assertions in the same spirit as test_build.py's
pinning tests for the skill's master prompts -- deterministic, no API calls, no
eval harness involved. They validate the *structure* of the command files
(existence, cross-references, phase separation); they cannot validate that a
live Claude Code session actually discovers or resolves them correctly -- that
requires a fresh interactive session and is out of reach of this test suite
(see #188's own open verification item).

TestInstallScriptInstallsCommands (#194) is the exception: it runs the real
install-skill.sh end-to-end against a fake HOME, because the bug it guards
against -- the installer extracting the skill but never placing the commands
anywhere Claude Code or Codex discovers them -- is exactly the kind of thing a
static content check cannot catch.
"""

import os
import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
COMMANDS_DIR = REPO_ROOT / "plugins" / "pdca-framework" / "commands"
SKILL_MD = REPO_ROOT / "skill" / "pdca-framework" / "SKILL.md"
SKILL_DIR = REPO_ROOT / "skill"
SKILL_ZIP = SKILL_DIR / "pdca-framework.skill"
INSTALL_SCRIPT = SKILL_DIR / "install-skill.sh"

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
            if match is None:
                self.fail(f"{name} does not quote a SKILL.md section header in the expected form")
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


class TestSkillZipPackagesCommands(unittest.TestCase):
    """The commands must ride inside pdca-framework.skill, not just live in
    plugins/ -- install-skill.sh only has the zip to work from (#194)."""

    def setUp(self):
        if not SKILL_ZIP.exists():
            self.skipTest(f"{SKILL_ZIP.name} not found -- run build-skill.sh first")

    def test_zip_contains_every_command_file(self):
        with zipfile.ZipFile(SKILL_ZIP) as archive:
            names = archive.namelist()
        for name in EXPECTED_COMMAND_FILES:
            with self.subTest(file=name):
                self.assertIn(f"pdca-framework/commands/{name}", names)

    def test_packaged_commands_match_source(self):
        with zipfile.ZipFile(SKILL_ZIP) as archive:
            for name in EXPECTED_COMMAND_FILES:
                packaged = archive.read(f"pdca-framework/commands/{name}").decode()
                source = (COMMANDS_DIR / name).read_text()
                self.assertEqual(packaged, source, f"packaged {name} doesn't match plugins/ source")


class TestInstallScriptInstallsCommands(unittest.TestCase):
    """install-skill.sh must place the packaged commands somewhere Claude Code
    or Codex actually discovers them, per scope (#194). Runs the real script
    end-to-end against a fake HOME so a regression fails loudly instead of
    silently leaving /pdca-plan unresolved after a normal install."""

    @classmethod
    def setUpClass(cls):
        if not SKILL_ZIP.exists():
            raise unittest.SkipTest(f"{SKILL_ZIP.name} not found -- run build-skill.sh first")

    def _run_install(self, scope, home, cwd=None):
        env = dict(os.environ, HOME=str(home))
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), scope],
            cwd=str(cwd or home),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"install-skill.sh {scope} failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        return result

    def test_personal_scope_installs_commands_to_claude_commands(self):
        with tempfile.TemporaryDirectory() as home:
            self._run_install("personal", Path(home))
            installed = sorted(p.name for p in (Path(home) / ".claude" / "commands").glob("*.md"))
            self.assertEqual(installed, sorted(EXPECTED_COMMAND_FILES))

    def test_codex_scope_installs_commands_to_codex_prompts(self):
        with tempfile.TemporaryDirectory() as home:
            self._run_install("codex", Path(home))
            installed = sorted(p.name for p in (Path(home) / ".codex" / "prompts").glob("*.md"))
            self.assertEqual(installed, sorted(EXPECTED_COMMAND_FILES))

    def test_project_scope_installs_commands_to_project_claude_commands(self):
        with tempfile.TemporaryDirectory() as home:
            project_dir = Path(home) / "project"
            project_dir.mkdir()
            self._run_install("project", Path(home), cwd=project_dir)
            installed = sorted(p.name for p in (project_dir / ".claude" / "commands").glob("*.md"))
            self.assertEqual(installed, sorted(EXPECTED_COMMAND_FILES))


if __name__ == "__main__":
    unittest.main()
