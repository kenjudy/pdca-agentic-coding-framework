"""
RED-step test for the shared builder extraction (issue #114).

Once `skill/build.py` exists (Step 2), it must expose the pinned interface
`build(core_dir: Path, skill_file: Path) -> Path` (see "build.py interface
(pinned)" in BUILD-EXTRACTION-PLAN.md) and produce a zip whose member set
matches EXPECTED_FILES (imported from test_build.py -- not duplicated by
hand). Member order is not asserted -- it has no bearing on installation.

This test intentionally imports a module named `build` that does not exist
yet. It is expected to fail with ModuleNotFoundError until Step 2 lands.
"""

import zipfile

from test_build import EXPECTED_FILES


def test_builder_produces_expected_manifest(tmp_path):
    import build

    core_dir = tmp_path / "pdca-framework"
    core_dir.mkdir()
    skill_file = tmp_path / "pdca-framework.skill"

    zip_path = build.build(core_dir=core_dir, skill_file=skill_file)

    with zipfile.ZipFile(zip_path) as zf:
        namelist = zf.namelist()

    assert sorted(namelist) == sorted(EXPECTED_FILES)
