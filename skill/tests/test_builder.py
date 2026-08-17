"""
RED-step test for the shared builder extraction (issue #114).

Once `skill/build.py` exists (Step 2), it must expose the pinned
one-parameter interface `build(skill_dir: Path) -> Path` (see "build.py
interface (pinned)" in BUILD-EXTRACTION-PLAN.md) and produce a zip whose
member set matches EXPECTED_FILES (imported from test_build.py -- not
duplicated by hand). Member order is not asserted -- it has no bearing on
installation.

The build writes references/ and the .skill zip to gitignored artifacts
that run-tests.sh regenerates every run, so this test calls build() against
the real skill/ directory (CLAUDE_SKILL_DIR from test_build.py) rather than
redirecting into a temp dir -- there is nothing hermetic to protect.

This test intentionally imports a module named `build` that does not exist
yet. It is expected to fail with ModuleNotFoundError until Step 2 lands.
"""

import zipfile

from test_build import CLAUDE_SKILL_DIR, EXPECTED_FILES, SKILL_FILE


def test_builder_produces_expected_manifest():
    import build

    zip_path = build.build(skill_dir=CLAUDE_SKILL_DIR)

    assert zip_path == SKILL_FILE

    with zipfile.ZipFile(zip_path) as zf:
        namelist = zf.namelist()

    assert sorted(namelist) == sorted(EXPECTED_FILES)
