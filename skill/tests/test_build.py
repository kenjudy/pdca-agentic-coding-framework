"""
Tests for build-skill.sh and the resulting pdca-framework.skill package.

Run from the skill/ directory:
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
PONYTAIL_ADDON_DIR = CLAUDE_SKILL_DIR / "pdca-framework" / "ponytail-addon" / "sources"
SUPERPOWERS_ADDON_DIR = CLAUDE_SKILL_DIR / "pdca-framework" / "superpowers-addon" / "sources"

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
    f"{SKILL_NAME}/references/ponytail-setup.md",
    f"{SKILL_NAME}/references/ponytail-workflow.md",
    f"{SKILL_NAME}/references/superpowers-setup.md",
    f"{SKILL_NAME}/references/superpowers-workflow.md",
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

PONYTAIL_SOURCE_FILES = [
    PONYTAIL_ADDON_DIR / "ponytail-setup.md",
    PONYTAIL_ADDON_DIR / "ponytail-workflow.md",
]

SUPERPOWERS_SOURCE_FILES = [
    SUPERPOWERS_ADDON_DIR / "superpowers-setup.md",
    SUPERPOWERS_ADDON_DIR / "superpowers-workflow.md",
]

# Optional third-party addons. Each slug's source files must exist, and every
# SKILL.md reference to that slug must be marked Optional. Add a slug here
# (plus an ADDON_SOURCE_FILES entry) when a new addon lands.
ADDON_SLUGS = ["beads", "ponytail", "superpowers"]

ADDON_SOURCE_FILES = {
    "beads": BEADS_SOURCE_FILES,
    "ponytail": PONYTAIL_SOURCE_FILES,
    "superpowers": SUPERPOWERS_SOURCE_FILES,
}

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

    def test_addon_source_files_exist(self):
        for slug, files in ADDON_SOURCE_FILES.items():
            for f in files:
                with self.subTest(addon=slug, file=f.name):
                    self.assertTrue(f.exists(), f"{slug.capitalize()} source file missing: {f}")

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

    def test_addon_references_are_optional(self):
        """All addon references must be either on a line with 'Optional' or inside
        a section whose heading contains 'Optional'."""
        # Build a map: line_number -> current section heading
        section_headings = {}
        current_heading = ""
        for i, line in enumerate(self.lines):
            if line.startswith("#"):
                current_heading = line
            section_headings[i] = current_heading

        for slug in ADDON_SLUGS:
            addon_refs = re.findall(rf"`(references/[^`]*{slug}[^`]*\.md)`", self.content)
            self.assertTrue(len(addon_refs) > 0, f"No {slug} references found in SKILL.md")

            for ref in addon_refs:
                matching_line_nums = [i for i, row in enumerate(self.lines) if ref in row]
                for lineno in matching_line_nums:
                    line = self.lines[lineno]
                    section = section_headings.get(lineno, "")
                    optional_on_line = "Optional" in line
                    optional_in_section = "Optional" in section
                    with self.subTest(addon=slug, ref=ref, line=line.strip()):
                        self.assertTrue(
                            optional_on_line or optional_in_section,
                            f"{slug.capitalize()} reference '{ref}' has no 'Optional' signal "
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
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"


EVAL_SCENARIOS_DIR = CLAUDE_SKILL_DIR / "eval" / "scenarios"
EVAL_BASELINES_DIR = CLAUDE_SKILL_DIR / "eval" / "baselines"


class TestEvalScenarios(unittest.TestCase):
    """Structural validation: every scenario JSON file must conform to the schema."""

    def test_superpowers_tdd_precedence_scopes_geval_to_called_shot(self):
        """#136/#148: GEval was off entirely; it is now on, scoped to what this scenario
        actually claims.

        Three measured rounds (34245608454, 34275465380, 34372905517) established that
        the Phase 2 judge, scored against the FULL rubric, docked this scenario for test
        ordering and for not executing tests -- neither of which it claims to measure, and
        the latter impossible in a single-turn harness. Scores swung 0.00-0.90 on
        behaviour the mechanical tier confirmed compliant at 17/18, 22/23, 17/18 across
        those same three runs. `skip_geval` silenced the noise but also silenced the one
        signal this scenario exists to carry: whether the called shot survives when
        superpowers' TDD skill offers a different ordering (test-then-confirm) than
        PDCA's (predict-then-test).

        #148 built scoping precisely so `skip_geval` would not have to be the last word.
        With it, this scenario is judged on `called-shot` alone -- the criterion the
        mechanical tier already confirms and the only one the scenario's input actually
        exercises. Left in scope, `degenerate-first` and `stub-discipline` would still
        dock unclaimed behaviour (the fixture's stub already hardcodes 0, so ordering
        isn't tested here), `refuse-to-skip-tests` and `no-completion-claim` describe
        situations this single-step input never presents, and `stub-based-red` needs test
        execution this single-turn harness cannot observe.
        """
        import json

        scenarios = json.loads((EVAL_SCENARIOS_DIR / "2_scenarios.json").read_text())
        target = [s for s in scenarios if s["scenario_id"] == "2-superpowers-tdd-precedence"]
        self.assertEqual(len(target), 1, "2-superpowers-tdd-precedence not found")
        signals = target[0]["expected_signals"]
        self.assertFalse(
            signals.get("skip_geval"),
            "2-superpowers-tdd-precedence should scope GEval via geval_criteria now that "
            "#148 exists, not silence it entirely with skip_geval",
        )
        self.assertEqual(
            signals.get("geval_criteria"),
            ["called-shot"],
            "2-superpowers-tdd-precedence should be judged only on the called-shot "
            "criterion -- the one behaviour its input actually exercises",
        )
        self.assertTrue(
            (signals.get("geval_criteria_reason") or "").strip(),
            "narrowing geval_criteria requires a stated reason (#148/eval/schema.py)",
        )

    def test_skip_geval_scenarios_still_assert_something(self):
        """A scenario with GEval off and no mechanical signal cannot fail.

        skip_geval is the only lever for silencing a judge that scores unclaimed
        dimensions, and it is all-or-nothing (#148). That makes it the obvious way to
        quiet an inconvenient red -- and a scenario quieted that way looks identical in
        the report to one that passed. This asserts the lever cannot be pulled that far.
        """
        import json

        for path in sorted(EVAL_SCENARIOS_DIR.glob("*.json")):
            scenarios = json.loads(path.read_text())
            if not isinstance(scenarios, list):
                scenarios = [scenarios]
            for scenario in scenarios:
                signals = scenario["expected_signals"]
                if not signals.get("skip_geval"):
                    continue
                with self.subTest(scenario=scenario["scenario_id"]):
                    has_mechanical = (
                        signals.get("must_contain")
                        or signals.get("must_not_contain")
                        or signals.get("called_shot_required")
                    )
                    self.assertTrue(
                        has_mechanical,
                        f"{scenario['scenario_id']} skips GEval and defines no mechanical "
                        "signal, so it asserts nothing and cannot fail -- it would report "
                        "as a pass forever",
                    )

    def test_all_done_guard_catches_sentence_initial_capitalization(self):
        """#116: "all done" missed the natural sentence-initial phrasing "All done."

        Demonstrated live in the issue: a model opening a response with "All done"
        evaded must_not_contain: ["all done"] entirely under case-sensitive matching,
        and after #112 this is 2-first-step's *only* mechanical signal.

        Fixed by adding the capitalized variant directly to the three affected
        scenarios' forbidden-phrase lists -- not by case-folding must_not_contain
        globally in eval/mechanical.py. A fresh adversarial critic pass on that
        approach found it broke two *other* scenarios that rely on capitalization
        to distinguish a directive statement from an incidental mention:
        1a-vague-goal's "Add an index" and 4-tdd-breakdown's "you should" both
        started matching compliant, lowercase incidental usage once must_not_contain
        was folded suite-wide. Scoping the fix to the three scenarios that actually
        need it leaves those two signals' case-sensitivity intact.
        """
        import json

        from eval.mechanical import check_mechanical

        scenarios = json.loads((EVAL_SCENARIOS_DIR / "2_scenarios.json").read_text())
        affected = {"2-first-step", "2-beads-ordering-capture", "2-ponytail-precedence"}
        targets = [s for s in scenarios if s["scenario_id"] in affected]
        self.assertEqual(len(targets), 3, "expected all three #116-affected scenarios")
        for scenario in targets:
            with self.subTest(scenario=scenario["scenario_id"]):
                results = check_mechanical(
                    "All done — the implementation is finished.",
                    scenario["expected_signals"],
                )
                mnc_results = [r for r in results if r.field.startswith("must_not_contain")]
                self.assertTrue(
                    any(not r.passed for r in mnc_results),
                    f"{scenario['scenario_id']} did not flag sentence-initial 'All done'",
                )

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

    def test_check_all_complete_scenario_includes_critic_pass_evidence(self):
        """3-all-complete must supply critic-pass evidence so the model can return Status: Complete.

        The Check prompt now requires an adversarial critic pass for any multi-file change.
        Without evidence in the input, the model will flag the critic pass as missing and
        return Status: Needs work, breaking the eval.
        """
        import json

        scenarios_file = EVAL_SCENARIOS_DIR / "3_scenarios.json"
        scenarios = json.loads(scenarios_file.read_text())
        all_complete = next(
            (s for s in scenarios if s.get("scenario_id") == "3-all-complete"), None
        )
        self.assertIsNotNone(all_complete, "3-all-complete scenario not found in 3_scenarios.json")
        assert all_complete is not None
        self.assertIn(
            "critic pass",
            all_complete["input"].lower(),
            "3-all-complete input must include evidence that an adversarial critic pass was run "
            "(the Check prompt requires one for multi-file changes)",
        )

    def test_check_has_critic_pass_missing_scenario(self):
        """A scenario must exist that tests the model blocks completion when no critic pass was run.

        The Check prompt requires an adversarial critic pass for multi-file changes.
        This scenario verifies the model correctly returns Status: Needs work when that
        evidence is absent from the input.
        """
        import json

        scenarios_file = EVAL_SCENARIOS_DIR / "3_scenarios.json"
        scenarios = json.loads(scenarios_file.read_text())
        ids = [s.get("scenario_id") for s in scenarios]
        self.assertIn(
            "3-critic-pass-missing",
            ids,
            "No scenario with id '3-critic-pass-missing' found in 3_scenarios.json — "
            "add one to cover the case where a multi-file change has no critic-pass evidence",
        )


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

    def test_run_tests_script_syncs_its_own_dependencies(self):
        """run-tests.sh must install the test and lint extras, not assume a provisioned venv.

        Issue #89. `uv run` auto-creates a venv holding only the project package —
        ruff and pytest live in optional extras it does not install. That fails outright
        on a fresh clone, and fails worse when an ambient ruff exists on PATH: the lint
        gate reports green while running a version below pyproject.toml's own declared
        floor. CI never caught either because its workflows sync the extras first.
        """
        script = (CLAUDE_SKILL_DIR / "run-tests.sh").read_text()
        self.assertIn(
            "uv sync",
            script,
            "run-tests.sh never runs 'uv sync' -- it relies on the venv being provisioned "
            "elsewhere, so a fresh clone has no ruff/pytest and an ambient ruff is used "
            "silently instead (issue #89)",
        )
        for extra in ("--extra test", "--extra lint"):
            self.assertIn(
                extra,
                script,
                f"run-tests.sh's sync does not request '{extra}', so the tools it then "
                "invokes with 'uv run' may resolve outside the venv (issue #89)",
            )


class TestDependencyFloors(unittest.TestCase):
    """pyproject.toml's declared floors must not understate what is actually locked.

    #127, #128 and #129 (dependabot) each correctly reported a real gap: uv.lock had
    already resolved anthropic 1.4.0, deepeval 4.2.2 and ruff 0.16.6 -- the earlier batch
    relock in this CHANGELOG's Dependency Updates section did that -- but the floors in
    `[project.optional-dependencies]` were never raised to match, so a `pip install` of
    this package with no lock (or an older compatible resolution) could silently receive
    versions below what the project actually builds and tests against.

    Generalized rather than hardcoded to today's three numbers: any future floor that
    drifts behind its own lock fails this the same way, not just these three packages.
    """

    @staticmethod
    def _floors():
        import re
        import tomllib

        data = tomllib.loads((CLAUDE_SKILL_DIR / "pyproject.toml").read_text())
        floors = {}
        for extra_deps in data["project"]["optional-dependencies"].values():
            for spec in extra_deps:
                m = re.match(r"^([A-Za-z0-9_.-]+)>=([0-9][0-9A-Za-z.]*)$", spec)
                if m:
                    floors[m.group(1).lower()] = m.group(2)
        return floors

    @staticmethod
    def _locked():
        import re

        text = (CLAUDE_SKILL_DIR / "uv.lock").read_text()
        locked = {}
        for m in re.finditer(r'name = "([^"]+)"\nversion = "([^"]+)"', text):
            locked[m.group(1).lower()] = m.group(2)
        return locked

    def test_declared_floor_matches_the_locked_version(self):
        """Not '<=' -- that is a tautology as long as uv.lock is valid at all: `uv lock`
        guarantees the resolved graph satisfies pyproject.toml's declared constraints, so
        floor <= locked can never fail while the lock resolves. It would pass with the
        exact gap #127-129 reported still wide open, which very nearly happened here.

        '==' is this project's own stated convention, confirmed against every OTHER
        floor before relying on it: pytest, python-dotenv and mypy already satisfy it.
        anthropic, deepeval and ruff are exactly the three that do not -- exactly the
        three dependabot flagged. The CHANGELOG's Dependency Updates entry describes the
        convention directly: "Floors raised and the lockfile relocked in one pass."
        """
        from packaging.version import Version

        floors, locked = self._floors(), self._locked()
        for name, floor in floors.items():
            if name not in locked:
                continue
            with self.subTest(package=name):
                self.assertEqual(
                    Version(floor),
                    Version(locked[name]),
                    f"pyproject.toml declares {name}>={floor}, but uv.lock resolves "
                    f"{name} {locked[name]} -- the floor has drifted behind what this "
                    f"project actually builds and tests against, so an install without "
                    f"the lock could silently receive an older, untested version",
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

    def test_current_version_matches_changelog(self):
        """README's Current Version must match the newest released version in CHANGELOG.md.

        The release checklist lists "update skill/README.md" as a manual step with nothing
        behind it -- it can be skipped and the release workflow still goes green. This test
        is the mechanism that step was missing.
        """
        readme_match = re.search(r"\*\*Current Version:\*\*\s*v(\d+\.\d+\.\d+)", self.content)
        self.assertIsNotNone(
            readme_match,
            "README.md has no '**Current Version:** vX.Y.Z' line to check",
        )
        assert readme_match is not None
        readme_version = readme_match.group(1)

        self.assertTrue(CHANGELOG_FILE.exists(), "CHANGELOG.md not found at repo root")
        changelog_content = CHANGELOG_FILE.read_text()
        # The newest RELEASED version is the first "## vX.Y.Z" heading. CHANGELOG.md
        # starts with "## Unreleased" (no version number, doesn't match) and later has
        # non-version "## " headings further down (e.g. "## What Changed") that also
        # don't match -- so the first match here is unambiguously the latest release.
        changelog_match = re.search(r"^## v(\d+\.\d+\.\d+)", changelog_content, re.MULTILINE)
        self.assertIsNotNone(
            changelog_match,
            "CHANGELOG.md has no '## vX.Y.Z' released-version heading to compare against",
        )
        assert changelog_match is not None
        changelog_version = changelog_match.group(1)

        self.assertEqual(
            readme_version,
            changelog_version,
            f"README Current Version (v{readme_version}) does not match the newest "
            f"released version in CHANGELOG.md (v{changelog_version}) -- update "
            "skill/README.md's '**Current Version:**' line",
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
        # Use a distinctive phrase from the master, not the first line which may change
        distinctive = "BEFORE STARTING STEP - ARCHITECTURAL SAFETY CHECK"
        self.assertIn(
            distinctive,
            packaged,
            "do-prompts.md doesn't contain expected master content",
        )

    def test_do_prompts_contains_the_first_executing_assertion_language(self):
        """#155's DO master edit must reach the packaged skill, not just the source.
        Mirrors test_do_prompts_contains_master_content's pattern."""
        packaged = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/do-prompts.md")
        self.assertIn(
            "the assertion expected to fail first",
            packaged,
            "do-prompts.md does not contain the #155 called-shot wording",
        )

    def test_check_prompts_contains_master_content(self):
        """check-prompts.md must contain master source content (injections may add to it).

        No test previously asserted this at all -- found while editing the CHECK master
        for #49/#165, the same class of gap #167 fixed for testing-anti-patterns.md.
        Mirrors test_do_prompts_contains_master_content's pattern: a substring pin, not
        exact equality, since check-review-probe is injected on top of the master here.
        """
        packaged = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/check-prompts.md")
        distinctive = "Review our original goal outcome and plan against our execution."
        self.assertIn(
            distinctive,
            packaged,
            "check-prompts.md doesn't contain expected master content",
        )

    def test_check_prompts_contains_the_evidence_and_autonomous_fallback_wording(self):
        """#49/#165's CHECK master edits must reach the packaged skill, not just the
        source. Mirrors test_do_prompts_contains_the_first_executing_assertion_language's
        pattern."""
        packaged = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/check-prompts.md")
        for distinctive, label in (
            ("All tests passing — show output", "#49's evidence requirement"),
            ("show git diff of implementation vs test files", "#49's evidence requirement"),
            ("no third-party review skill", "#165's autonomous-mode fallback"),
        ):
            with self.subTest(label=label):
                self.assertIn(
                    distinctive,
                    packaged,
                    f"check-prompts.md does not contain {label} wording",
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

    def test_testing_anti_patterns_matches_master(self):
        """#167: nothing previously asserted that build.py copies
        "2. Do/Testing Anti-Patterns.md" into the packaged skill at all -- unlike
        do-prompts.md and working-agreements.md, which have a propagation test.
        (check-prompts.md and act-prompts.md turned out NOT to have one either when this
        was checked again while fixing #49/#165 -- this file's own docstring overclaimed
        that when it was written. test_check_prompts_contains_master_content below closes
        that gap for check-prompts.md; act-prompts.md's remains open.)
        build.py's own COPIED_FROM_MASTER comment says this file is copied verbatim, not
        license-stripped, so exact equality (not a substring pin) is the right guard -- it
        fails on truncation or staleness anywhere in the file, not just around one item,
        and needs no update when the master's content changes shape.

        Mirrors test_working_agreements_matches_master's pattern, without the license
        split that file's master needs and this one's does not.
        """
        packaged = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/testing-anti-patterns.md")
        master = (REPO_ROOT / "2. Do" / "Testing Anti-Patterns.md").read_text()
        self.assertEqual(
            packaged.strip(),
            master.strip(),
            "testing-anti-patterns.md content doesn't match its master source",
        )

    def test_addon_files_match_source(self):
        """Addon files in package should match their source files exactly."""
        for slug, files in ADDON_SOURCE_FILES.items():
            for src_path in files:
                pkg_path = f"{SKILL_NAME}/references/{src_path.name}"
                with self.subTest(addon=slug, file=pkg_path):
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

    def test_plan_prompts_directs_steps_to_do_phase(self):
        """plan-prompts.md must explicitly direct each implementation step to use the DO phase prompt."""
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/plan-prompts.md")
        self.assertIn(
            "DO phase prompt",
            content,
            "plan-prompts.md missing instruction to use DO phase prompt for each step",
        )

    def test_plan_prompts_contains_plan_mode_probe(self):
        """plan-prompts.md must contain the plan-mode-probe injection."""
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/plan-prompts.md")
        probe = (CLAUDE_ADDON_DIR / "plan-mode-probe.md").read_text().strip()
        self.assertIn(probe[:60], content, "plan-prompts.md missing plan-mode-probe injection")

    def test_do_prompts_contains_commit_after_green(self):
        """do-prompts.md must contain a commit-after-GREEN instruction."""
        content = read_zip_file(SKILL_FILE, f"{SKILL_NAME}/references/do-prompts.md")
        self.assertIn(
            "commit",
            content[content.find("Green phase"):content.find("Refactor")].lower(),
            "do-prompts.md missing commit-after-green instruction",
        )

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

    def test_called_shot_requires_predicting_the_first_executing_assertion(self):
        """#155: the called shot's 'Expected failure' field named the most meaningful
        assertion in a multi-assertion test, not the one the runner reports first. When
        those differ, a correct test's RED reads as a misprediction and the STOP rule
        fires for the wrong reason -- or worse, trains the operator to wave it through,
        which erodes the rule for the case it exists to catch.

        Checked against the master source directly (unconditional, no build needed).
        assertTrue rather than assertIn per #143.
        """
        master = (REPO_ROOT / "2. Do" / "2. Test Drive the Change.md").read_text()
        self.assertTrue(
            "the assertion expected to fail first" in master,
            "the DO master's CALLED SHOT block does not ask for the first-executing "
            "assertion specifically, so a loose prediction against a different "
            "assertion in the same test cannot be told apart from a genuine "
            "misprediction (#155)",
        )
        self.assertTrue(
            "ordered so a secondary one runs before the one that expresses the "
            "behavior under test" in master,
            "the DO master's STOP-rule sentence does not name assertion ordering as a "
            "possible cause of a RED mismatch, only 'testing the wrong thing' (#155)",
        )
        self.assertTrue(
            "aggregate failures per test" in master,
            "the DO master's STOP-rule sentence has no qualification for assertion "
            "styles that aggregate failures (subTest, soft assertions) -- for those, "
            "'ran first' is the wrong question and the ordering-based rule above "
            "would misfire on the repo's own subTest-based tests (found in adversarial "
            "review of #155)",
        )

    def test_testing_anti_patterns_names_the_loose_called_shot_pattern(self):
        """#155's own suggestion: name the pattern so it is citable in retros, the way
        #8 (Partial-Instance Coverage) has been used as diagnostic vocabulary all
        cycle rather than re-explained from scratch each time.

        Pins the Rule paragraph, not just the heading. An earlier version of this test
        pinned only the heading and was found, by adversarial review, to pass against
        an empty section -- mutation-tested afterward here to confirm it no longer does.
        """
        master = (REPO_ROOT / "2. Do" / "Testing Anti-Patterns.md").read_text()
        self.assertTrue(
            "## 9. Loose Called Shot" in master,
            "Testing Anti-Patterns.md has no item 9 for a called shot that predicts "
            "the most meaningful assertion rather than the first-executing one (#155)",
        )
        self.assertTrue(
            "Predict the exact message of the first assertion that will fail, not "
            "the most meaningful one" in master,
            "item 9's Rule paragraph is missing -- a heading alone does not tell "
            "anyone what to do differently (#155)",
        )
        self.assertTrue(
            "the mismatch is the predicted assertion being absent from the report, "
            "not out of order" in master,
            "item 9's Diagnosis does not qualify for assertion styles that aggregate "
            "failures per test, so it states a false universal -- 'the runner stops "
            "at the first failing assertion' is untrue for subTest, soft assertions, "
            "and aggregate_failures, which this repo's own test suite uses (found in "
            "adversarial review of #155)",
        )

    def test_testing_anti_patterns_item_9_matches_the_established_layout(self):
        """Items 1-8 each open with a '---' separator and get a Quick Check line;
        item 9 initially had neither, which is precisely item 8's own anti-pattern
        (a document that indexes its items in several places, updated in only one)."""
        master = (REPO_ROOT / "2. Do" / "Testing Anti-Patterns.md").read_text()
        self.assertTrue(
            "---\n\n## 9. Loose Called Shot" in master,
            "item 9 has no '---' separator before it, unlike every other item in "
            "this file (#155)",
        )
        self.assertTrue(
            "(see #9)" in master,
            "Quick Check Before Committing has no line referencing item 9, unlike "
            "every other numbered item (#155)",
        )

    def test_do_master_cross_references_the_loose_called_shot_anti_pattern(self):
        """Items 7 and 8 are both cross-referenced from the DO master at the exact
        point their guidance applies (see '2. Do/2. Test Drive the Change.md:60,72,129').
        Item 9 had no reference from anywhere outside its own section."""
        master = (REPO_ROOT / "2. Do" / "2. Test Drive the Change.md").read_text()
        self.assertTrue(
            "references/testing-anti-patterns.md` #9" in master,
            "the DO master's CALLED SHOT section does not cross-reference "
            "testing-anti-patterns.md #9, unlike the #7 and #8 references elsewhere "
            "in this same file (#155)",
        )

    def test_working_agreements_asks_which_assertion_fired(self):
        """The operator-side half of #155: an intervention question matching the
        format already used by every other line in this section, so 'the called shot
        drifted' is as askable in the moment as 'where's the failing test first'."""
        master = (REPO_ROOT / "Human Working Agreements.md").read_text()
        self.assertTrue(
            "Which assertion did you predict, and which one fired?" in master,
            "Human Working Agreements.md's Process Discipline section has no "
            "intervention question for a called shot that predicted the wrong "
            "assertion (#155)",
        )

    def test_working_agreements_requires_verifying_a_prior_commands_result(self):
        """#138: a command chain where one step fails silently must not let a later
        step assert something the failed step never accomplished.

        Concrete incident: `bd update --append-notes` (a heredoc) failed with a bash
        syntax error; the three commands in the invocation were not `&&`-chained, so
        execution continued past the failure into two `bd close` calls whose
        --reason text claimed the notes had been recorded. They had not. The agent
        caught this only by later re-running `bd show` against its own claim rather
        than trusting it.

        The working agreements already require verifying test expectations (item 4)
        and RED before GREEN in the DO master, but neither generalizes to CLI/tool
        orchestration -- a beads state change, a multi-step shell command, any case
        where step N's success is assumed rather than checked before step N+1 asserts
        something about it. Checked against the master source directly rather than the
        built package, so this runs in the default suite with no build step required --
        unlike TestSkillPackage, which skips entirely when the .skill zip is absent.
        assertTrue rather than assertIn, per #143: assertIn dumps the entire file into
        the failure message and buries the one line that matters.
        """
        master = (REPO_ROOT / "Human Working Agreements.md").read_text()
        self.assertTrue(
            "VERIFY BEFORE CLAIMING" in master,
            "Human Working Agreements.md has no rule requiring a prior command's "
            "actual result be checked before a later command, commit, or close "
            "reason asserts something depended on it (#138)",
        )

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

    def test_run_evals_script_builds_and_syncs(self):
        """run-evals.sh must build the skill and sync the eval extra before running.

        The harness reads the BUILT prompt files under pdca-framework/references/,
        which are gitignored artifacts regenerated by build-skill.sh. run-tests.sh
        builds first; run-evals.sh did not, so on any tree without a prior build every
        scenario died with FileNotFoundError on do-prompts.md before reaching the API.

        That failure is far worse than a crash: each shot is reported as "did not pass",
        which is indistinguishable in a summary count from the model actually failing
        the scenario. An eval harness that cannot run reads exactly like an eval harness
        delivering a verdict. Same shape as issue #89, in the script next door.
        """
        script = (CLAUDE_SKILL_DIR / "run-evals.sh").read_text()
        self.assertIn(
            "build-skill.sh",
            script,
            "run-evals.sh never builds the skill, so pdca-framework/references/ may not "
            "exist and every scenario fails with FileNotFoundError before any API call -- "
            "reported as a failing scenario, not as a broken harness",
        )
        self.assertIn(
            "--extra eval",
            script,
            "run-evals.sh does not sync the eval extra, so deepeval/anthropic may be absent",
        )

    def test_push_policy_is_consistent_across_agent_files(self):
        """CLAUDE.md and AGENTS.md must agree on when an agent may push.

        Both are auto-loaded instruction files -- CLAUDE.md by Claude Code, AGENTS.md by
        Codex -- and they gave opposite directives on the most consequential action either
        takes. CLAUDE.md said "NEVER say 'ready to push when you are' -- push yourself";
        AGENTS.md said "Do NOT push without explicit human instruction". Nothing could
        detect the divergence, because each file is only ever read by the agent it governs.

        The policy is: the operator approves the push in a human-in-the-loop session, and
        an agent pushes on its own only when explicitly instructed to act autonomously.
        Both halves must appear in both files, so dropping either one fails here.
        """
        for name in ("CLAUDE.md", "AGENTS.md"):
            content = (REPO_ROOT / name).read_text()
            lowered = content.lower()
            # assertTrue rather than assertIn: assertIn renders the entire file into the
            # failure message, which buries the one sentence that matters.
            with self.subTest(file=name, half="approval default"):
                self.assertTrue(
                    "approv" in lowered,
                    f"{name} does not state that pushing requires operator approval by default",
                )
            with self.subTest(file=name, half="autonomous carve-out"):
                self.assertTrue(
                    "autonomous" in lowered,
                    f"{name} does not state the exception -- an agent pushes on its own only "
                    "when explicitly instructed to act autonomously",
                )
            with self.subTest(file=name, half="no unconditional self-push"):
                self.assertFalse(
                    "push yourself" in lowered,
                    f"{name} instructs unconditional self-push, contradicting the approval "
                    "default and the other agent instruction file",
                )

    def test_settings_json_has_no_machine_specific_path(self):
        """.claude/settings.json is checked in, so it must run on every clone.

        Its PreToolUse hook contained an absolute path to one contributor's Mac. On any
        other machine the `cd` fails, the `&&` chain short-circuits, and the trailing
        `exit 0` reports success -- an advisory mypy gate that has never been able to fire
        anywhere but one laptop, while looking configured to everyone.
        """
        settings = REPO_ROOT / ".claude" / "settings.json"
        self.assertTrue(settings.exists(), ".claude/settings.json missing")
        content = settings.read_text()
        for home_prefix in ("/Users/", "/home/", "C:\\Users"):
            with self.subTest(prefix=home_prefix):
                self.assertNotIn(
                    home_prefix,
                    content,
                    f"settings.json hardcodes a machine-specific path containing "
                    f"'{home_prefix}'. It is checked in, so it must resolve paths relative "
                    "to the repository -- otherwise the hook silently no-ops for everyone else",
                )

    def test_typecheck_invocation_is_shared(self):
        """CI and the pre-commit hook must type-check via one shared script.

        They previously carried separate mypy argument lists and had already diverged --
        the hook still named `tests/test_build.py` while CI named six targets. That is
        #114 in miniature: two copies of one procedure, drifting silently because only one
        of them ever ran.
        """
        script = CLAUDE_SKILL_DIR / "typecheck.sh"
        self.assertTrue(script.exists(), "skill/typecheck.sh missing -- no shared invocation")

        workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text()
        self.assertIn("typecheck.sh", workflow, "CI does not use the shared typecheck script")

        settings = (REPO_ROOT / ".claude" / "settings.json").read_text()
        self.assertIn(
            "typecheck.sh",
            settings,
            "the pre-commit hook does not use the shared typecheck script, so its module "
            "list can drift from CI's again",
        )

    def test_ci_mypy_covers_every_top_level_module(self):
        """typecheck.sh must name every top-level module under skill/.

        The list is hand-maintained, so a new module is type-checked only if someone
        remembers to widen it. build.py went unchecked until #126 noticed, and
        check_changelog.py was never added at all -- it shipped in #134 having been run
        only locally. Both are the same slip: a gate whose coverage silently fails to grow
        with the code it guards. Asserted against typecheck.sh rather than the workflow,
        since that script is now the single invocation CI and the hook both call.
        """
        invocation = (CLAUDE_SKILL_DIR / "typecheck.sh").read_text()

        modules = sorted(
            p.name for p in CLAUDE_SKILL_DIR.glob("*.py") if not p.name.startswith("_")
        )
        self.assertTrue(modules, "no top-level modules found to check")
        for module in modules:
            with self.subTest(module=module):
                self.assertIn(
                    module,
                    invocation,
                    f"{module} exists under skill/ but is absent from typecheck.sh, so it "
                    "is never type-checked -- by CI or by the pre-commit hook",
                )

    def test_run_evals_script_distinguishes_a_dead_harness(self):
        """run-evals.sh must classify "nothing was measured" apart from "a scenario failed".

        A shot that dies before reaching the API produces no scored result, but pytest
        exits non-zero either way -- so a caller counting exit codes reports a crash and
        a genuine failure identically. That is how "5 shot(s); 5 did not pass" came to be
        reported for a harness that never called the API once (#131 Step 0), reading
        exactly like a confirmed hypothesis.
        """
        script = (CLAUDE_SKILL_DIR / "run-evals.sh").read_text()
        self.assertIn(
            "check_eval_ran.py",
            script,
            "run-evals.sh does not check whether the harness actually produced a verdict, "
            "so a crash and a scenario failure are indistinguishable in its exit code",
        )
        self.assertIn(
            "-newer",
            script,
            "the check must be scoped to reports from THIS run; eval/results/ accumulates, "
            "so an earlier scored report would mask a run that scored nothing",
        )

    def test_eval_workflow_separates_harness_errors_from_failures(self):
        """evals.yml must count a dead harness separately from a failing scenario.

        run-evals.sh exits 2 when it produced no verdict and 1 when a scenario genuinely
        failed. The workflow has to act on that distinction; counting every non-zero exit
        as "did not pass" is the wording that made a harness which never called the API
        report "5 shot(s); 5 did not pass" and read as a confirmed hypothesis.

        Asserting on the exit code rather than on the word "harness": the word already
        appeared in an unrelated warning string, so a keyword check passed vacuously.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "evals.yml"
        content = workflow.read_text()
        self.assertIn(
            "harness_errors",
            content,
            "evals.yml does not track harness errors separately from scenario failures, "
            "so a run that measured nothing is reported as a run that measured failure",
        )
        self.assertIn(
            "-eq 2",
            content,
            "evals.yml does not branch on run-evals.sh's exit code 2, which is how a "
            "harness that produced no verdict is signalled",
        )

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

    def test_ci_runs_the_eval_import_smoke_test(self):
        """test.yml must have a job that installs the eval extra and runs the smoke test.

        tests/test_eval_imports.py is excluded from the default suite, so nothing runs it
        unless CI does. An excluded test with no job behind it is worse than no test --
        it looks like coverage while providing none (issue #122).
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        self.assertTrue(workflow.exists(), ".github/workflows/test.yml missing")
        content = workflow.read_text()
        self.assertIn(
            "tests/test_eval_imports.py",
            content,
            "no CI job runs tests/test_eval_imports.py, which the default suite excludes -- "
            "the eval harness's dependency surface would be untested everywhere",
        )
        self.assertIn(
            "--extra eval",
            content,
            "CI runs the eval import smoke test without syncing '--extra eval', so it would "
            "fail on a missing deepeval rather than testing anything",
        )

    def test_judge_model_is_not_constructed_at_module_scope(self):
        """tests/test_evals.py must be importable without a credential (#156).

        deepeval raises during AnthropicModel construction when no key is present, so a
        module-scope judge makes the file unimportable, uncollectable, and unanalysable
        without a secret -- which is why every cheap check has skipped it and why every
        edit to it has been unverifiable except by paying for an eval run.

        Checked by parsing the source rather than importing it. Importing is the thing
        that does not work, and this test has to run in the default suite, which installs
        neither deepeval nor a key.
        """
        import ast

        source = (CLAUDE_SKILL_DIR / "tests" / "test_evals.py").read_text()
        offenders = []
        for node in ast.parse(source).body:
            # A function body runs when called, not when the module is imported, so a
            # construction inside one is the fix rather than the defect.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for call in ast.walk(node):
                if not isinstance(call, ast.Call):
                    continue
                func = call.func
                name = getattr(func, "id", None) or getattr(func, "attr", None)
                if name == "AnthropicModel":
                    offenders.append(getattr(node, "lineno", "?"))
        self.assertEqual(
            offenders,
            [],
            f"tests/test_evals.py constructs AnthropicModel at module scope (line(s) "
            f"{offenders}), so importing the module requires an API key",
        )

    def test_eval_collection_needs_no_api_key(self):
        """The observable consequence of the fix, and the reason to make it.

        The collection step shipped with a dummy key because the module could not be
        imported without one. Once the judge is built lazily that workaround is dead
        weight, and leaving it would hide a regression: if module-scope construction came
        back, the step would keep passing on the dummy key and say nothing.
        """
        workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text()
        step = workflow[workflow.index("Collect the eval suite without running it"):]
        step = step[: step.index("--collect-only")]
        self.assertNotIn(
            "ANTHROPIC_API_KEY",
            step,
            "the eval-collection step still sets ANTHROPIC_API_KEY, so it cannot detect a "
            "return to module-scope judge construction -- it would pass on the dummy key",
        )

    def test_ci_collects_the_eval_suite(self):
        """Something must import tests/test_evals.py without spending money.

        It is excluded from the default suite (it makes real API calls), so a broken
        import or bad node id there surfaces only when someone dispatches a run -- half an
        hour and a few dollars later.

        It also cannot be imported without a credential: it builds AnthropicModel at module
        import time. That is why every cheap check has skipped this file, and why the CI
        step passes a deliberately fake key -- collection executes nothing.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        content = workflow.read_text()
        self.assertTrue(
            "--collect-only" in content and "tests/test_evals.py" in content,
            "no CI job collects tests/test_evals.py, so an import error in the eval suite "
            "is only discoverable by paying for an eval run",
        )

    def test_ci_exercises_the_reporter_against_installed_eval_dependencies(self):
        """The eval-extra job must also run the reporter tests.

        The reporter records the installed deepeval and anthropic versions so a report
        can serve as a baseline (issue #122). The default suite installs neither, so
        every provenance assertion there exercises only the "not installed" branch. If
        no job runs those tests with the packages present, the branch that produces the
        version string a human will actually read is never executed anywhere -- the
        same shape as the pre-commit hook that could not run outside one machine (#142).
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        content = workflow.read_text()
        self.assertTrue(
            "tests/test_evals_reporter.py" in content,
            "no CI job runs tests/test_evals_reporter.py with the eval extra installed, so "
            "the reporter's real version-recording path is never exercised -- it would only "
            "ever be tested against absent packages",
        )

    def test_release_workflow_checks_version_consistency(self):
        """release.yml must run check_release_version.py against the tag it is building.

        The checker being correct is worth nothing if nothing calls it -- an unwired
        guard is the same silent pass it exists to prevent. This asserts the wiring,
        and that the tag is actually passed rather than the script being run bare.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        self.assertTrue(workflow.exists(), ".github/workflows/release.yml missing")
        content = workflow.read_text()
        self.assertIn(
            "check_release_version.py",
            content,
            "release.yml does not run skill/check_release_version.py, so a tag that matches "
            "neither README.md nor CHANGELOG.md would publish a mislabeled release",
        )
        self.assertIn(
            "github.ref_name",
            content,
            "release.yml runs check_release_version.py without passing github.ref_name, "
            "so it cannot compare anything against the tag being released",
        )

    def test_ci_enforces_the_changelog_rule_on_pull_requests(self):
        """test.yml must run check_changelog.py against the PR base.

        CONTRIBUTING.md's per-PR CHANGELOG rule had no mechanism behind it and was
        routinely missed. The check needs a diff, which exists only on a pull request,
        so it cannot live in the unit suite -- but the wiring can be asserted here.
        fetch-depth: 0 is load-bearing: without full history the merge base is absent
        and the diff would be wrong rather than absent, which is worse.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "test.yml"
        content = workflow.read_text()
        self.assertIn(
            "check_changelog.py",
            content,
            "test.yml does not run check_changelog.py, so CONTRIBUTING.md's CHANGELOG "
            "requirement stays a documented gate with nothing behind it",
        )
        self.assertIn(
            "fetch-depth: 0",
            content,
            "the changelog job needs full history for the merge base; a shallow clone "
            "produces a wrong diff rather than an obvious failure",
        )

    def test_eval_workflow_exists_and_passes_api_key(self):
        """A dispatchable workflow must run the eval harness with the API key wired through.

        The eval suite is the only mechanism that can tell us whether a prompt change
        helped, and it needs a credential no contributor should paste into a session.
        Running it from CI keeps ANTHROPIC_API_KEY in GitHub secrets. A workflow that
        exists but never passes the secret through would look configured and fail only
        after paying for checkout and dependency install, so both are asserted.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "evals.yml"
        self.assertTrue(
            workflow.exists(),
            ".github/workflows/evals.yml missing - the eval harness has no way to run "
            "without a contributor supplying a key by hand",
        )
        content = workflow.read_text()
        self.assertIn(
            "workflow_dispatch",
            content,
            "evals.yml must be manually dispatchable - eval runs cost money and must "
            "never fire automatically on push or pull_request",
        )
        for forbidden in ("on: push", "pull_request:"):
            self.assertNotIn(
                forbidden,
                content,
                f"evals.yml declares '{forbidden}', which would spend API budget on every "
                "push or PR; eval runs are manual by design",
            )
        self.assertIn(
            "secrets.ANTHROPIC_API_KEY",
            content,
            "evals.yml does not pass secrets.ANTHROPIC_API_KEY, so the run would fail at "
            "the first API call having already spent setup time",
        )

    def test_eval_workflow_prints_reports_to_the_log(self):
        """evals.yml must echo the eval reports into the job log, not only upload them.

        The reports carry the recorded model responses, and eval/README.md requires
        diagnosing a failure from the response rather than the pass rate. Uploading them
        as an artifact alone puts them behind an authenticated download that agents and
        CI consumers may not be able to reach -- leaving the shot count as the only
        visible result, which is precisely the thing that must not be trusted alone.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "evals.yml"
        self.assertTrue(workflow.exists(), ".github/workflows/evals.yml missing")
        content = workflow.read_text()
        self.assertIn(
            "eval/results/*.md",
            content,
            "evals.yml never prints the eval reports, so the recorded responses are only "
            "reachable via authenticated artifact download and the shot count becomes the "
            "only readable result",
        )

    def test_release_workflow_grants_contents_write(self):
        """release.yml's job must declare permissions: contents: write.

        Without it GITHUB_TOKEN gets the repository default (read-only) and
        softprops/action-gh-release fails with "403 Resource not accessible by
        integration - create-a-release". Every release run in this repo's history
        failed exactly this way and each release was published by hand instead, so
        the red workflow never blocked anything and nobody had reason to look.
        """
        workflow = REPO_ROOT / ".github" / "workflows" / "release.yml"
        self.assertTrue(workflow.exists(), ".github/workflows/release.yml missing")
        content = workflow.read_text()
        self.assertIn(
            "permissions:",
            content,
            "release.yml declares no 'permissions:' block, so GITHUB_TOKEN falls back to the "
            "repository default (read-only) and creating the GitHub Release 403s",
        )
        self.assertRegex(
            content,
            r"permissions:\s*\n\s+contents:\s*write",
            "release.yml does not grant 'contents: write', which is the permission "
            "softprops/action-gh-release needs to create a release and upload the .skill asset",
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

    def test_do_beads_addon_has_git_commit_after_green(self):
        content = self._read_source("do-beads-addon.md")
        green_pos = content.find("After RED")
        self.assertNotEqual(green_pos, -1, "do-beads-addon.md missing 'After RED' section")
        green_section = content[green_pos:]
        self.assertIn(
            "git commit",
            green_section,
            "do-beads-addon.md missing git commit block after GREEN",
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


class TestEvalBaselines(unittest.TestCase):
    """A tracked baseline must exist, and must be attributable (#122).

    CLAUDE.md's Validating Prompt Changes step 1 says to "check skill/eval/results/ for
    the baseline scores". That directory is gitignored (.gitignore:28) and `git log --all`
    over it is empty -- it has never been tracked. The instruction has therefore been
    inoperable on every fresh clone and in CI for as long as it has existed, and #122's
    own closing procedure ("compare against the baselines in skill/eval/results/") had no
    left-hand side.

    eval/results/ cannot simply be un-ignored: every run writes a fresh timestamped report
    there, so tracking it would leave the tree dirty after each run -- the churn pattern
    uv.lock already produced. eval/baselines/ holds deliberately promoted reports only.
    """

    @staticmethod
    def _scenario_ids() -> list[str]:
        import json

        ids: list[str] = []
        for path in sorted(EVAL_SCENARIOS_DIR.glob("*.json")):
            scenarios = json.loads(path.read_text())
            if not isinstance(scenarios, list):
                scenarios = [scenarios]
            ids.extend(s["scenario_id"] for s in scenarios)
        return ids

    @staticmethod
    def _baseline_texts():
        if not EVAL_BASELINES_DIR.is_dir():
            return []
        return [p.read_text() for p in sorted(EVAL_BASELINES_DIR.glob("report_*.md"))]

    def test_baseline_exists_for_every_scenario(self):
        """Reuses check_eval_ran.scored_scenarios rather than re-parsing the Summary
        table: that parser already distinguishes a scored row from a crashed run's empty
        table, which is exactly the distinction a baseline must not blur."""
        import sys

        sys.path.insert(0, str(CLAUDE_SKILL_DIR))
        from check_eval_ran import scored_scenarios

        covered = set()
        for text in self._baseline_texts():
            covered.update(scored_scenarios(text))

        missing = sorted(set(self._scenario_ids()) - covered)
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} scenario(s) have no baseline in skill/eval/baselines/: "
            f"{', '.join(missing)}",
        )

    def test_declared_geval_criteria_exist_in_their_rubric(self):
        """A criteria id that no rubric defines must fail here, not mid-run (#148).

        `assemble` raises on an unknown id, but that happens inside an eval run costing
        real money and taking half an hour. Catching it in the unit suite makes a typo a
        five-second failure instead.

        Deliberately NOT asserting that a narrowed scenario keeps mechanical signals.
        Narrowing leaves GEval active with at least one criterion, so the scenario still
        has teeth -- unlike skip_geval, which removes the tier entirely and is why
        test_skip_geval_scenarios_still_assert_something exists. Requiring mechanical
        signals here would forbid narrowing on scenarios that legitimately have none.
        """
        import json
        import sys

        sys.path.insert(0, str(CLAUDE_SKILL_DIR))
        from eval.rubrics import RUBRICS

        for path in sorted(EVAL_SCENARIOS_DIR.glob("*.json")):
            scenarios = json.loads(path.read_text())
            if not isinstance(scenarios, list):
                scenarios = [scenarios]
            for scenario in scenarios:
                declared = scenario["expected_signals"].get("geval_criteria")
                if not declared:
                    continue
                with self.subTest(scenario=scenario["scenario_id"]):
                    module = RUBRICS[scenario["prompt_id"]]
                    unknown = sorted(set(declared) - set(module.CRITERIA_ITEMS))
                    self.assertEqual(
                        unknown,
                        [],
                        f"{scenario['scenario_id']} names criteria its rubric does not "
                        f"define: {unknown}; available: {sorted(module.CRITERIA_ITEMS)}",
                    )

    def test_baselines_dir_is_not_gitignored(self):
        """The mechanism that stops #122's defect recurring.

        The whole problem was an instruction naming a path that git never tracked. Adding
        eval/baselines/ to .gitignore later would reproduce it exactly, silently, and the
        instruction would keep reading as though it worked.
        """
        result = subprocess.run(
            ["git", "check-ignore", "-q", "skill/eval/baselines/"],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        # git check-ignore exits 0 when the path IS ignored.
        self.assertNotEqual(
            result.returncode,
            0,
            "skill/eval/baselines/ is gitignored, so the baselines the instructions point "
            "at would not exist on a fresh clone or in CI -- the exact defect of #122",
        )

    def test_instruction_files_point_at_the_tracked_baselines_dir(self):
        """CLAUDE.md and SUPERVISION-PROTOCOL.md both told readers to get baseline scores
        from skill/eval/results/, which has never been tracked."""
        for rel in ("CLAUDE.md", "skill/SUPERVISION-PROTOCOL.md"):
            with self.subTest(instruction_file=rel):
                text = (REPO_ROOT / rel).read_text()
                self.assertIn(
                    "skill/eval/baselines/",
                    text,
                    f"{rel} does not name the tracked baselines directory, so its "
                    "baseline instruction points at gitignored output that is absent on "
                    "any fresh clone and in CI (#122)",
                )

    def test_every_baseline_records_the_versions_that_produced_it(self):
        """A baseline that does not say what produced it cannot be compared against --
        the defect that made #122 unanswerable in retrospect. #145 made the reporter
        record this; this asserts a promoted baseline actually carries it."""
        texts = self._baseline_texts()
        self.assertTrue(texts, "no baseline reports in skill/eval/baselines/")
        for path, text in zip(sorted(EVAL_BASELINES_DIR.glob("report_*.md")), texts):
            with self.subTest(baseline=path.name):
                self.assertIn(
                    "deepeval:",
                    text,
                    f"{path.name} records no deepeval version, so the scores in it cannot "
                    "be attributed to a dependency set (#122)",
                )
