"""
Tests for build-skill.sh and the resulting pdca-framework.skill package.

Run from the claude-skill/ directory:
    python3 tests/test_build.py

Or to run a fresh build before testing:
    bash build-skill.sh && python3 tests/test_build.py
"""

import os
import re
import subprocess
import unittest
import zipfile
from pathlib import Path

CLAUDE_SKILL_DIR = Path(__file__).parent.parent
REPO_ROOT = CLAUDE_SKILL_DIR.parent
SKILL_FILE = CLAUDE_SKILL_DIR / "pdca-framework.skill"
SKILL_SRC = CLAUDE_SKILL_DIR / "pdca-framework" / "SKILL.md"
BEADS_ADDON_DIR = CLAUDE_SKILL_DIR / "pdca-framework" / "beads-addon" / "sources"

SKILL_NAME = "pdca-framework"

EXPECTED_FILES = [
    f"{SKILL_NAME}/SKILL.md",
    f"{SKILL_NAME}/references/plan-prompts.md",
    f"{SKILL_NAME}/references/do-prompts.md",
    f"{SKILL_NAME}/references/check-prompts.md",
    f"{SKILL_NAME}/references/act-prompts.md",
    f"{SKILL_NAME}/references/working-agreements.md",
    f"{SKILL_NAME}/references/plan-beads-addon.md",
    f"{SKILL_NAME}/references/do-beads-addon.md",
    f"{SKILL_NAME}/references/check-beads-addon.md",
    f"{SKILL_NAME}/references/act-beads-addon.md",
    f"{SKILL_NAME}/references/beads-setup.md",
    f"{SKILL_NAME}/references/beads-workflow.md",
    f"{SKILL_NAME}/references/testing-anti-patterns.md",
    f"{SKILL_NAME}/references/scripts/export-requirements.sh",
]

MASTER_FILES = [
    REPO_ROOT / "1. Plan" / "1a Analyze to determine approach for achieving the goal.md",
    REPO_ROOT / "1. Plan" / "1b Create a detailed implementation plan.md",
    REPO_ROOT / "2. Do" / "2. Test Drive the Change.md",
    REPO_ROOT / "2. Do" / "Testing Anti-Patterns.md",
    REPO_ROOT / "3. Check" / "3. Completeness Check.md",
    REPO_ROOT / "4. Act" / "4. Retrospect for continuous improvement.md",
    REPO_ROOT / "Human Working Agreements.md",
]

BEADS_SOURCE_FILES = [
    BEADS_ADDON_DIR / "plan-beads-addon.md",
    BEADS_ADDON_DIR / "do-beads-addon.md",
    BEADS_ADDON_DIR / "check-beads-addon.md",
    BEADS_ADDON_DIR / "act-beads-addon.md",
    BEADS_ADDON_DIR / "beads-setup.md",
    BEADS_ADDON_DIR / "beads-workflow.md",
]

CLAUDE_ADDON_DIR = CLAUDE_SKILL_DIR / "pdca-framework" / "claude-addon" / "injections"
CLAUDE_INJECTION_FILES = [
    "goal-probe.md",
    "plan-mode-probe.md",
    "think-probe.md",
    "do-think-probe.md",
    "check-review-probe.md",
    "act-retro-probes.md",
]


def read_zip_file(zip_path, member):
    with zipfile.ZipFile(zip_path) as zf:
        return zf.read(member).decode("utf-8")


def zip_names(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        return set(zf.namelist())


class TestSourceFiles(unittest.TestCase):
    """Verify all source files exist before build runs."""

    def test_master_obsidian_files_exist(self):
        for f in MASTER_FILES:
            with self.subTest(file=f.name):
                self.assertTrue(f.exists(), f"Master file missing: {f}")

    def test_beads_addon_source_files_exist(self):
        for f in BEADS_SOURCE_FILES:
            with self.subTest(file=f.name):
                self.assertTrue(f.exists(), f"Beads source file missing: {f}")

    def test_skill_md_source_exists(self):
        self.assertTrue(SKILL_SRC.exists(), f"SKILL.md source missing: {SKILL_SRC}")

    def test_build_script_exists(self):
        self.assertTrue(
            (CLAUDE_SKILL_DIR / "build-skill.sh").exists(), "build-skill.sh missing"
        )


class TestSkillMdSource(unittest.TestCase):
    """Validate the SKILL.md source file structure."""

    def setUp(self):
        self.content = SKILL_SRC.read_text()
        self.lines = self.content.splitlines()

    def test_has_frontmatter_name(self):
        self.assertRegex(self.content, r"^---\nname:", "Missing frontmatter name field")

    def test_has_frontmatter_description(self):
        self.assertIn("description:", self.content, "Missing frontmatter description")

    def test_skill_name_is_pdca_framework(self):
        match = re.search(r"^name:\s*(.+)$", self.content, re.MULTILINE)
        self.assertIsNotNone(match, "Could not parse skill name")
        assert match is not None
        self.assertEqual(match.group(1).strip(), "pdca-framework")

    def test_under_500_lines(self):
        self.assertLessEqual(
            len(self.lines),
            500,
            f"SKILL.md is {len(self.lines)} lines — exceeds progressive disclosure guideline of 500",
        )

    def test_all_referenced_files_declared(self):
        """Every references/xxx.md mention in SKILL.md must be in EXPECTED_FILES."""
        refs = re.findall(r"`(references/[^`]+\.md)`", self.content)
        for ref in refs:
            with self.subTest(ref=ref):
                qualified = f"{SKILL_NAME}/{ref}"
                msg = f"SKILL.md references '{ref}' but '{qualified}' is not in EXPECTED_FILES"
                self.assertIn(qualified, EXPECTED_FILES, msg)

    def test_beads_references_are_optional(self):
        """All beads references must be either on a line with 'Optional' or inside
        a section whose heading contains 'Optional'."""
        beads_refs = re.findall(r"`(references/[^`]*beads[^`]*\.md)`", self.content)
        self.assertTrue(len(beads_refs) > 0, "No beads references found in SKILL.md")

        # Build a map: line_number -> current section heading
        section_headings = {}
        current_heading = ""
        for i, line in enumerate(self.lines):
            if line.startswith("#"):
                current_heading = line
            section_headings[i] = current_heading

        for ref in beads_refs:
            matching_line_nums = [i for i, row in enumerate(self.lines) if ref in row]
            for lineno in matching_line_nums:
                line = self.lines[lineno]
                section = section_headings.get(lineno, "")
                optional_on_line = "Optional" in line
                optional_in_section = "Optional" in section
                with self.subTest(ref=ref, line=line.strip()):
                    self.assertTrue(
                        optional_on_line or optional_in_section,
                        f"Beads reference '{ref}' has no 'Optional' signal "
                        f"on its line or in its section heading ('{section.strip()}')",
                    )

    def test_description_is_third_person(self):
        """Marketplace requirement: description must be third-person, not imperative."""
        match = re.search(r"^description:\s*(.+)$", self.content, re.MULTILINE)
        self.assertIsNotNone(match, "Could not parse description")
        assert match is not None
        description = match.group(1).strip()
        imperative_phrases = ["Use when", "Use this when", "Run when", "Apply when"]
        for phrase in imperative_phrases:
            self.assertNotIn(
                phrase,
                description,
                f"Description contains imperative '{phrase}' — must be third-person for marketplace compliance",
            )

    def test_description_under_200_chars(self):
        """Marketplace requirement: description field must be ≤200 characters."""
        match = re.search(r"^description:\s*(.+)$", self.content, re.MULTILINE)
        self.assertIsNotNone(match, "Could not parse description")
        assert match is not None
        description = match.group(1).strip()
        self.assertLessEqual(
            len(description),
            200,
            f"Description is {len(description)} chars — marketplace limit is 200",
        )

    def test_skill_md_retains_license(self):
        """SKILL.md is human-facing — its license block must be preserved."""
        self.assertIn(
            "## License & Attribution",
            self.content,
            "SKILL.md license block was removed — it should be kept (human-facing)",
        )

    def test_four_pdca_phases_documented(self):
        for phase in ["PLAN", "DO", "CHECK", "ACT"]:
            with self.subTest(phase=phase):
                self.assertIn(phase, self.content, f"Phase {phase} not found in SKILL.md")


README_FILE = CLAUDE_SKILL_DIR / "README.md"


EVAL_SCENARIOS_DIR = CLAUDE_SKILL_DIR / "eval" / "scenarios"


class TestEvalScenarios(unittest.TestCase):
    """Structural validation: every scenario JSON file must conform to the schema."""

    def test_scenario_files_valid_against_schema(self):
        """All JSON files in eval/scenarios/ must pass validate_scenario.
        Passes vacuously until scenario files are added in Step 4."""
        import json

        from eval.schema import validate_scenario

        scenario_files = list(EVAL_SCENARIOS_DIR.glob("*.json"))
        for scenario_file in scenario_files:
            with self.subTest(file=scenario_file.name):
                scenarios = json.loads(scenario_file.read_text())
                if not isinstance(scenarios, list):
                    scenarios = [scenarios]
                for scenario in scenarios:
                    validate_scenario(scenario)


class TestProjectSetup(unittest.TestCase):
    """Validate uv-based Python project infrastructure."""

    def test_eval_pytest_marker_registered(self):
        """pytest --markers must list the eval marker — confirms pyproject.toml registers it."""
        result = subprocess.run(
            ["python3", "-m", "pytest", "--markers", "--ignore=tests/test_evals.py"],
            cwd=str(CLAUDE_SKILL_DIR),
            capture_output=True,
            text=True,
        )
        self.assertIn(
            "@pytest.mark.eval",
            result.stdout,
            "pytest does not recognise 'eval' marker — add it to [tool.pytest.ini_options] in pyproject.toml",
        )

    def test_run_tests_script_uses_uv_runner(self):
        """run-tests.sh must delegate to uv run pytest, not bare python3."""
        script = CLAUDE_SKILL_DIR / "run-tests.sh"
        self.assertIn(
            "uv run",
            script.read_text(),
            "run-tests.sh must invoke 'uv run pytest', not bare 'python3'",
        )


class TestReadme(unittest.TestCase):
    """Validate README quality for marketplace distribution."""

    def setUp(self):
        if not README_FILE.exists():
            self.skipTest("README.md not found")
        self.content = README_FILE.read_text()

    def test_no_placeholder_links(self):
        """README must not contain unfilled bracket placeholders outside code blocks."""
        # Strip fenced code blocks (```...```) before checking
        prose = re.sub(r"```.*?```", "", self.content, flags=re.DOTALL)
        # Strip inline code spans
        prose = re.sub(r"`[^`]+`", "", prose)
        # Matches [some text] not followed by ( or [ — orphaned link text
        orphaned = re.findall(r"\[[^\]]+\](?![\(\[])", prose)
        # Exclude markdown checkboxes like [ ] or [x]
        orphaned = [m for m in orphaned if not re.match(r"^\[[ xX]\]$", m)]
        self.assertEqual(
            orphaned,
            [],
            f"README contains unfilled placeholder link(s) outside code blocks: {orphaned}",
        )

    def test_has_semantic_version(self):
        """README must have a semantic version number, not a vague date string."""
        self.assertRegex(
            self.content,
            r"v\d+\.\d+\.\d+",
            "README must contain a semantic version (e.g. v1.0.0)",
        )


class TestSkillPackage(unittest.TestCase):
    """Validate the built pdca-framework.skill zip package."""

    def setUp(self):
        if not SKILL_FILE.exists():
            self.skipTest(f"{SKILL_FILE.name} not found — run build-skill.sh first")

    def test_skill_file_is_valid_zip(self):
        self.assertTrue(zipfile.is_zipfile(SKILL_FILE), "pdca-framework.skill is not a valid zip")

    def test_zip_has_wrapper_folder(self):
        """Marketplace requirement: ZIP root must be a folder matching the skill name."""
        names = zip_names(SKILL_FILE)
        for name in names:
            with self.subTest(entry=name):
                self.assertTrue(
                    name.startswith("pdca-framework/"),
                    f"ZIP entry '{name}' is not inside the pdca-framework/ wrapper folder",
                )

    def test_contains_exactly_expected_files(self):
        names = zip_names(SKILL_FILE)
        for expected in EXPECTED_FILES:
            with self.subTest(file=expected):
                self.assertIn(expected, names, f"Missing from package: {expected}")

    def test_no_build_artifact_paths(self):
        """Ensure no references/build/ intermediate paths leaked into the zip."""
        names = zip_names(SKILL_FILE)
        for name in names:
            with self.subTest(file=name):
                self.assertNotIn(
                    "references/build/",
                    name,
                    f"Build artifact path found in package: {name}",
                )

    def test_skill_md_in_package_under_500_lines(self):
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/SKILL.md")
        lines = content.splitlines()
        self.assertLessEqual(
            len(lines),
            500,
            f"Packaged SKILL.md is {len(lines)} lines — exceeds 500",
        )

    def test_plan_prompts_contains_1a_content(self):
        """plan-prompts.md should include content from the 1a master."""
        plan = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/plan-prompts.md")
        master_1a = (REPO_ROOT / "1. Plan" / "1a Analyze to determine approach for achieving the goal.md").read_text()
        # Check a distinctive phrase from 1a is present
        first_meaningful_line = next(
            ln.strip() for ln in master_1a.splitlines() if ln.strip() and not ln.startswith("#")
        )
        self.assertIn(
            first_meaningful_line[:60],
            plan,
            "plan-prompts.md doesn't appear to contain 1a master content",
        )

    def test_plan_prompts_contains_1b_content(self):
        """plan-prompts.md should include content from the 1b master."""
        plan = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/plan-prompts.md")
        master_1b = (REPO_ROOT / "1. Plan" / "1b Create a detailed implementation plan.md").read_text()
        first_meaningful_line = next(
            ln.strip() for ln in master_1b.splitlines() if ln.strip() and not ln.startswith("#")
        )
        self.assertIn(
            first_meaningful_line[:60],
            plan,
            "plan-prompts.md doesn't appear to contain 1b master content",
        )

    def test_do_prompts_contains_master_content(self):
        """do-prompts.md must contain master source content (injections may add to it)."""
        packaged = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/do-prompts.md")
        master = (REPO_ROOT / "2. Do" / "2. Test Drive the Change.md").read_text()
        # Use a distinctive phrase from the master, not the first line which may change
        distinctive = "BEFORE STARTING STEP - ARCHITECTURAL SAFETY CHECK"
        self.assertIn(
            distinctive,
            packaged,
            "do-prompts.md doesn't contain expected master content",
        )

    def test_working_agreements_matches_master(self):
        packaged = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/working-agreements.md")
        master = (REPO_ROOT / "Human Working Agreements.md").read_text()
        master_stripped = master.split("## License & Attribution")[0]
        self.assertEqual(
            packaged.strip(),
            master_stripped.strip(),
            "working-agreements.md content doesn't match license-stripped master source",
        )

    def test_beads_addon_files_match_source(self):
        """Beads addon files in package should match their source files exactly."""
        addon_map = {
            f"{SKILL_NAME}/references/plan-beads-addon.md": BEADS_ADDON_DIR / "plan-beads-addon.md",
            f"{SKILL_NAME}/references/do-beads-addon.md": BEADS_ADDON_DIR / "do-beads-addon.md",
            f"{SKILL_NAME}/references/check-beads-addon.md": BEADS_ADDON_DIR / "check-beads-addon.md",
            f"{SKILL_NAME}/references/act-beads-addon.md": BEADS_ADDON_DIR / "act-beads-addon.md",
            f"{SKILL_NAME}/references/beads-setup.md": BEADS_ADDON_DIR / "beads-setup.md",
            f"{SKILL_NAME}/references/beads-workflow.md": BEADS_ADDON_DIR / "beads-workflow.md",
        }
        for pkg_path, src_path in addon_map.items():
            with self.subTest(file=pkg_path):
                if not src_path.exists():
                    self.skipTest(f"Source file missing: {src_path}")
                packaged = read_zip_file(SKILL_FILE, pkg_path)
                source = src_path.read_text()
                self.assertEqual(
                    packaged.strip(),
                    source.strip(),
                    f"{pkg_path} doesn't match source {src_path.name}",
                )

    def test_all_skill_md_references_resolvable(self):
        """Every references/xxx.md link in packaged SKILL.md must exist in the zip."""
        skill_content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/SKILL.md")
        refs = re.findall(r"`(references/[^`]+\.md)`", skill_content)
        names = zip_names(SKILL_FILE)
        for ref in refs:
            with self.subTest(ref=ref):
                qualified = f"{SKILL_NAME}/{ref}"
                self.assertIn(qualified, names, f"SKILL.md references '{ref}' but '{qualified}' is not in the package")

    def test_no_empty_files(self):
        with zipfile.ZipFile(SKILL_FILE) as zf:
            for info in zf.infolist():
                with self.subTest(file=info.filename):
                    self.assertGreater(
                        info.file_size,
                        0,
                        f"Empty file in package: {info.filename}",
                    )

    def test_license_stripped_from_prompt_files(self):
        """License & Attribution blocks must not appear in built prompt files.
        They add ~760 tokens of in-context overhead with no value to Claude."""
        prompt_files = [
            f"{SKILL_NAME}/references/plan-prompts.md",
            f"{SKILL_NAME}/references/do-prompts.md",
            f"{SKILL_NAME}/references/check-prompts.md",
            f"{SKILL_NAME}/references/act-prompts.md",
            f"{SKILL_NAME}/references/working-agreements.md",
        ]
        for pkg_path in prompt_files:
            with self.subTest(file=pkg_path):
                content = read_zip_file(SKILL_FILE, pkg_path)
                self.assertNotIn(
                    "## License & Attribution",
                    content,
                    f"{pkg_path} still contains a License & Attribution block — "
                    "strip_license() should remove it at build time",
                )


class TestClaudeInjections(unittest.TestCase):
    """Validate Claude-specific injection system: source files exist, markers replaced."""

    def test_injection_source_files_exist(self):
        for fname in CLAUDE_INJECTION_FILES:
            with self.subTest(file=fname):
                path = CLAUDE_ADDON_DIR / fname
                self.assertTrue(path.exists(), f"Claude injection source missing: {path}")

    def test_injection_source_files_non_empty(self):
        for fname in CLAUDE_INJECTION_FILES:
            with self.subTest(file=fname):
                path = CLAUDE_ADDON_DIR / fname
                if not path.exists():
                    self.skipTest(f"Source file missing: {path}")
                self.assertGreater(path.stat().st_size, 0, f"Claude injection file is empty: {fname}")

    def test_no_inject_markers_remain_in_built_files(self):
        """All CLAUDE_INJECT markers must be replaced during build — none should survive."""
        built_files = [
            f"{SKILL_NAME}/references/plan-prompts.md",
            f"{SKILL_NAME}/references/do-prompts.md",
            f"{SKILL_NAME}/references/check-prompts.md",
            f"{SKILL_NAME}/references/act-prompts.md",
        ]
        for pkg_path in built_files:
            with self.subTest(file=pkg_path):
                content = read_zip_file(SKILL_FILE, pkg_path)
                self.assertNotIn(
                    "CLAUDE_INJECT",
                    content,
                    f"{pkg_path} still contains an unresolved CLAUDE_INJECT marker",
                )

    def test_plan_prompts_contains_plan_mode_probe(self):
        """plan-prompts.md must contain the plan-mode-probe injection."""
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/plan-prompts.md")
        probe = (CLAUDE_ADDON_DIR / "plan-mode-probe.md").read_text().strip()
        self.assertIn(probe[:60], content, "plan-prompts.md missing plan-mode-probe injection")

    def test_do_prompts_contains_think_probe(self):
        """do-prompts.md must contain the do-think-probe injection."""
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/do-prompts.md")
        probe = (CLAUDE_ADDON_DIR / "do-think-probe.md").read_text().strip()
        self.assertIn(probe[:60], content, "do-prompts.md missing do-think-probe injection")

    def test_act_prompts_contains_retro_probe(self):
        """act-prompts.md must contain the act-retro-probes injection."""
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/act-prompts.md")
        probe = (CLAUDE_ADDON_DIR / "act-retro-probes.md").read_text().strip()
        self.assertIn(probe[:60], content, "act-prompts.md missing act-retro-probes injection")


class TestBuildScript(unittest.TestCase):
    """Run the build script once and verify its outputs.

    Uses setUpClass to build a single time — avoids running build-skill.sh
    three times (~30s each) for independent output checks.
    """

    _build_result: "subprocess.CompletedProcess[str] | None" = None

    @classmethod
    def setUpClass(cls):
        beads_skill = CLAUDE_SKILL_DIR / "pdca-framework-beads.skill"
        if beads_skill.exists():
            beads_skill.unlink()
        cls._build_result = subprocess.run(
            ["bash", "build-skill.sh"],
            cwd=str(CLAUDE_SKILL_DIR),
            capture_output=True,
            text=True,
        )

    def test_build_script_exits_zero(self):
        assert self._build_result is not None, "setUpClass did not run"
        self.assertEqual(
            self._build_result.returncode,
            0,
            f"build-skill.sh failed:\nSTDOUT:\n{self._build_result.stdout}\nSTDERR:\n{self._build_result.stderr}",
        )

    def test_build_produces_skill_file(self):
        self.assertTrue(SKILL_FILE.exists(), "build-skill.sh did not produce pdca-framework.skill")

    def test_build_does_not_produce_beads_skill(self):
        """The retired pdca-framework-beads.skill should not be regenerated."""
        beads_skill = CLAUDE_SKILL_DIR / "pdca-framework-beads.skill"
        self.assertFalse(
            beads_skill.exists(),
            "build-skill.sh produced pdca-framework-beads.skill — it should only build one unified package",
        )


class TestHookInfrastructure(unittest.TestCase):
    """Verify git hook infrastructure files exist and are correctly structured."""

    def test_run_tests_script_exists(self):
        self.assertTrue(
            (CLAUDE_SKILL_DIR / "run-tests.sh").exists(),
            "run-tests.sh missing — canonical test runner for hooks and CI",
        )

    def test_run_tests_script_is_executable(self):
        script = CLAUDE_SKILL_DIR / "run-tests.sh"
        if not script.exists():
            self.skipTest("run-tests.sh not found")
        self.assertTrue(os.access(script, os.X_OK), "run-tests.sh must be executable")

    def test_run_evals_script_is_executable(self):
        script = CLAUDE_SKILL_DIR / "run-evals.sh"
        if not script.exists():
            self.skipTest("run-evals.sh not found")
        self.assertTrue(os.access(script, os.X_OK), "run-evals.sh must be executable")

    def test_run_evals_script_uses_eval_marker(self):
        script = CLAUDE_SKILL_DIR / "run-evals.sh"
        if not script.exists():
            self.skipTest("run-evals.sh not found")
        content = script.read_text()
        self.assertIn("-m eval", content, "run-evals.sh must filter tests with -m eval marker")

    def test_pre_commit_hook_template_exists(self):
        self.assertTrue(
            (REPO_ROOT / "hooks" / "pre-commit").exists(),
            "hooks/pre-commit template missing at repo root",
        )

    def test_pre_commit_hook_calls_run_tests(self):
        hook = REPO_ROOT / "hooks" / "pre-commit"
        if not hook.exists():
            self.skipTest("hooks/pre-commit not found")
        self.assertIn(
            "run-tests.sh",
            hook.read_text(),
            "pre-commit hook must delegate to run-tests.sh",
        )

    def test_pre_commit_hook_exits_zero(self):
        """Pre-commit hook must warn only (exit 0) — never block commits."""
        hook = REPO_ROOT / "hooks" / "pre-commit"
        if not hook.exists():
            self.skipTest("hooks/pre-commit not found")
        self.assertNotIn(
            "exit 1",
            hook.read_text(),
            "pre-commit hook must exit 0 (warn-only) — use CI to enforce failures",
        )

    def test_install_hooks_script_exists(self):
        self.assertTrue(
            (REPO_ROOT / "install-hooks.sh").exists(),
            "install-hooks.sh missing at repo root — needed to install hooks into .git/hooks/",
        )

    def test_github_actions_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        self.assertTrue(
            workflow.exists(),
            ".github/workflows/test.yml missing — CI workflow required",
        )

    def test_github_actions_triggers_on_push_and_pr(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        if not workflow.exists():
            self.skipTest(".github/workflows/test.yml not found")
        content = workflow.read_text()
        self.assertIn("push:", content, "Workflow missing 'push:' trigger")
        self.assertIn("pull_request:", content, "Workflow missing 'pull_request:' trigger")

    def test_github_actions_runs_test_suite(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        if not workflow.exists():
            self.skipTest(".github/workflows/test.yml not found")
        self.assertIn(
            "run-tests.sh",
            workflow.read_text(),
            "Workflow must invoke run-tests.sh",
        )


class TestBeadsTemplateCompleteness(unittest.TestCase):
    """Beads addon templates must include acceptance criteria and resumption context."""

    def _read_source(self, filename):
        return (BEADS_ADDON_DIR / filename).read_text()

    # --- plan-beads-addon.md ---

    def test_plan_epic_template_has_acceptance_criteria(self):
        content = self._read_source("plan-beads-addon.md")
        self.assertIn(
            "## Acceptance Criteria",
            content,
            "plan-beads-addon.md epic template must include an Acceptance Criteria section",
        )

    def test_plan_epic_template_has_out_of_scope(self):
        content = self._read_source("plan-beads-addon.md")
        self.assertIn(
            "## Out of Scope",
            content,
            "plan-beads-addon.md epic template must include an Out of Scope section",
        )

    def test_plan_epic_template_has_resumption_context(self):
        content = self._read_source("plan-beads-addon.md")
        self.assertIn(
            "## Resumption Context",
            content,
            "plan-beads-addon.md epic template must include a Resumption Context section",
        )

    # --- do-beads-addon.md ---

    def test_do_task_template_has_before_state(self):
        content = self._read_source("do-beads-addon.md")
        self.assertIn(
            "Before:",
            content,
            "do-beads-addon.md task template must include a Before: field",
        )

    def test_do_task_template_has_after_state(self):
        content = self._read_source("do-beads-addon.md")
        self.assertIn(
            "After:",
            content,
            "do-beads-addon.md task template must include an After: field",
        )

    def test_do_task_template_has_done_when(self):
        content = self._read_source("do-beads-addon.md")
        self.assertIn(
            "Done when:",
            content,
            "do-beads-addon.md task template must include a Done when: field",
        )

    # --- check-beads-addon.md ---

    def test_check_verifies_acceptance_criteria(self):
        content = self._read_source("check-beads-addon.md")
        self.assertIn(
            "Acceptance criteria",
            content,
            "check-beads-addon.md verification checklist must include an acceptance criteria step",
        )

    # --- beads-workflow.md ---

    def test_workflow_plan_section_has_acceptance_criteria(self):
        content = self._read_source("beads-workflow.md")
        self.assertIn(
            "Acceptance Criteria",
            content,
            "beads-workflow.md PLAN section must include Acceptance Criteria template",
        )

    def test_workflow_do_section_has_done_when(self):
        content = self._read_source("beads-workflow.md")
        self.assertIn(
            "Done when:",
            content,
            "beads-workflow.md DO section must include Done when: field in task template",
        )


class TestExecutorBaselineMode(unittest.TestCase):
    """run_phase must support include_skill_prompt=False for baseline comparison."""

    def test_run_phase_without_skill_prompt_sends_no_system_message(self):
        from unittest.mock import MagicMock, patch

        from eval.executor import run_phase

        mock_response = MagicMock()
        mock_response.content[0].text = "response text"
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        phase_path = Path("/fake/plan-prompts.md")
        with patch.object(Path, "read_text", return_value="system content"):
            run_phase(phase_path, "scenario input", include_skill_prompt=False, _client=mock_client)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        self.assertNotIn(
            "system",
            call_kwargs,
            "run_phase with include_skill_prompt=False must not pass a 'system' argument to the client",
        )

    def test_run_phase_with_skill_prompt_still_passes_system_message(self):
        """Non-regression: default behavior must be unchanged."""
        from unittest.mock import MagicMock, patch

        from eval.executor import run_phase

        mock_response = MagicMock()
        mock_response.content[0].text = "response text"
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        phase_path = Path("/fake/plan-prompts.md")
        with patch.object(Path, "read_text", return_value="system content"):
            run_phase(phase_path, "scenario input", _client=mock_client)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        self.assertIn(
            "system",
            call_kwargs,
            "run_phase default (include_skill_prompt=True) must still pass 'system' to the client",
        )
        self.assertEqual(call_kwargs["system"], "system content")


class TestShotStats(unittest.TestCase):
    """compute_shot_stats must return mean and sample stddev from shot scores."""

    def test_compute_shot_stats_returns_mean_and_stddev(self):
        from eval.reporter import compute_shot_stats

        result = compute_shot_stats([0.9, 0.5, 0.7])

        self.assertIn("shot_mean", result, "compute_shot_stats must return 'shot_mean' key")
        self.assertIn("shot_stddev", result, "compute_shot_stats must return 'shot_stddev' key")
        self.assertAlmostEqual(result["shot_mean"], 0.7, places=3)
        self.assertAlmostEqual(result["shot_stddev"], 0.2, places=1)

    def test_compute_shot_stats_single_score_has_zero_stddev(self):
        from eval.reporter import compute_shot_stats

        result = compute_shot_stats([0.85])

        self.assertAlmostEqual(result["shot_mean"], 0.85, places=3)
        self.assertEqual(result["shot_stddev"], 0.0)

    def test_compute_shot_stats_identical_scores_have_zero_stddev(self):
        from eval.reporter import compute_shot_stats

        result = compute_shot_stats([0.8, 0.8, 0.8])

        self.assertAlmostEqual(result["shot_mean"], 0.8, places=3)
        self.assertEqual(result["shot_stddev"], 0.0)


class TestBeadsWorkflowContent(unittest.TestCase):
    """Validate human-in-the-loop alignment of beads workflow and setup files."""

    def _read_source(self, filename):
        return (BEADS_ADDON_DIR / filename).read_text()

    def test_export_script_exists(self):
        """export-requirements.sh must exist in beads-addon/scripts/."""
        script = BEADS_ADDON_DIR.parent / "scripts" / "export-requirements.sh"
        self.assertTrue(script.exists(), f"export-requirements.sh not found at {script}")

    def test_export_script_is_executable(self):
        """export-requirements.sh must be executable."""
        script = BEADS_ADDON_DIR.parent / "scripts" / "export-requirements.sh"
        if not script.exists():
            self.skipTest("export-requirements.sh not found")
        self.assertTrue(os.access(script, os.X_OK), "export-requirements.sh must be executable")

    def test_workflow_has_requirements_export_section(self):
        """beads-workflow.md must have an Export Requirements Document section."""
        content = self._read_source("beads-workflow.md")
        self.assertIn(
            "Export Requirements Document",
            content,
            "beads-workflow.md missing 'Export Requirements Document' section",
        )

    def test_setup_has_postinit_alignment(self):
        """beads-setup.md must have a Post-Init CLAUDE.md alignment subsection."""
        content = self._read_source("beads-setup.md")
        self.assertIn(
            "Post-Init: Align CLAUDE.md",
            content,
            "beads-setup.md missing 'Post-Init: Align CLAUDE.md' subsection",
        )

    def test_setup_mcp_has_status_check(self):
        """MCP section of beads-setup.md must contain pip3 show beads-mcp before install command."""
        content = self._read_source("beads-setup.md")
        mcp_start = content.find("MCP Server")
        self.assertNotEqual(mcp_start, -1, "MCP Server section not found in beads-setup.md")
        mcp_section = content[mcp_start:]
        pip_show_pos = mcp_section.find("pip3 show beads-mcp")
        pip_install_pos = mcp_section.find("pip3 install beads-mcp")
        self.assertNotEqual(
            pip_show_pos, -1,
            "MCP section missing 'pip3 show beads-mcp' status check",
        )
        self.assertLess(
            pip_show_pos,
            pip_install_pos,
            "pip3 show beads-mcp status check must appear before pip3 install beads-mcp",
        )

    def test_setup_has_preflight_section(self):
        """beads-setup.md must have Pre-flight Check before System Requirements."""
        content = self._read_source("beads-setup.md")
        preflight_pos = content.find("## Pre-flight Check")
        requirements_pos = content.find("## System Requirements")
        self.assertNotEqual(preflight_pos, -1, "beads-setup.md missing 'Pre-flight Check' section")
        self.assertNotEqual(requirements_pos, -1, "beads-setup.md missing 'System Requirements' section")
        self.assertLess(
            preflight_pos,
            requirements_pos,
            "Pre-flight Check must appear before System Requirements",
        )

    def test_resume_has_brew_outdated(self):
        """Resume a Session section must contain brew outdated beads dolt."""
        content = self._read_source("beads-workflow.md")
        resume_start = content.find("## Resume a Session")
        self.assertNotEqual(resume_start, -1, "Resume a Session section not found")
        next_section = content.find("\n## ", resume_start + 1)
        resume_section = content[resume_start:next_section] if next_section != -1 else content[resume_start:]
        self.assertIn(
            "brew outdated beads dolt",
            resume_section,
            "Resume a Session section missing 'brew outdated beads dolt' version check",
        )

    def test_workflow_has_resume_section(self):
        """beads-workflow.md must have a Resume a Session heading."""
        content = self._read_source("beads-workflow.md")
        self.assertIn(
            "## Resume a Session",
            content,
            "beads-workflow.md missing 'Resume a Session' section",
        )

    def test_resume_before_pdca_mapping(self):
        """Resume a Session section must appear before PDCA -> Beads Mapping."""
        content = self._read_source("beads-workflow.md")
        resume_pos = content.find("## Resume a Session")
        mapping_pos = content.find("## PDCA")
        self.assertNotEqual(resume_pos, -1, "Resume a Session section not found")
        self.assertNotEqual(mapping_pos, -1, "PDCA mapping section not found")
        self.assertLess(
            resume_pos,
            mapping_pos,
            "Resume a Session section must appear before the PDCA mapping table",
        )

    def test_act_addon_committed_not_stored(self):
        """act-beads-addon.md closing checklist must say 'Committed to git' not 'Stored in git'."""
        content = self._read_source("act-beads-addon.md")
        self.assertNotIn(
            "Stored in git",
            content,
            "act-beads-addon.md still uses old 'Stored in git' phrasing",
        )
        self.assertIn(
            "Committed to git",
            content,
            "act-beads-addon.md must use 'Committed to git -- push when ready per working agreements'",
        )

    def test_workflow_no_bare_git_push(self):
        """Git Integration section must not contain git push as an autonomous instruction."""
        content = self._read_source("beads-workflow.md")
        git_section_start = content.find("## Git Integration")
        self.assertNotEqual(git_section_start, -1, "Git Integration section not found")
        git_section = content[git_section_start:]
        self.assertNotIn(
            "git push",
            git_section,
            "beads-workflow.md contains a bare git push instruction in Git Integration section",
        )

    def test_setup_gitignore_no_mandate(self):
        """beads-setup.md must not mandate committing all of .beads/ as a regular project file."""
        content = self._read_source("beads-setup.md")
        self.assertNotIn(
            "Commit `.beads/` like any other project file",
            content,
            "beads-setup.md incorrectly mandates committing all of .beads/ as a regular project file",
        )

    def test_setup_gitignore_presents_both_strategies(self):
        """beads-setup.md post-init section must present both git-native and Dolt-native sharing strategies."""
        content = self._read_source("beads-setup.md")
        init_pos = content.find("## Initializing Beads in a Project")
        self.assertNotEqual(init_pos, -1, "Initializing Beads in a Project section not found")
        init_section = content[init_pos:]
        self.assertIn(
            "bd dolt push",
            init_section,
            "Post-init section must mention 'bd dolt push' as the Dolt-native sharing strategy",
        )
        self.assertIn(
            "issues.jsonl",
            init_section,
            "Post-init section must mention 'issues.jsonl' as the git-native sharing option",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
