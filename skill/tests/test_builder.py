"""
RED-step test for the shared builder extraction (issue #114).

Once `skill/build.py` exists (Step 2), it must be able to build the
pdca-framework skill package into an arbitrary output directory and produce a
zip whose member list exactly matches EXPECTED_FILES (imported from
test_build.py -- not duplicated by hand).

This test intentionally imports a module named `build` that does not exist
yet. It is expected to fail with ModuleNotFoundError until Step 2 lands.
"""

import zipfile

from test_build import EXPECTED_FILES


def test_builder_produces_expected_manifest(tmp_path):
    import build

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    zip_path = build.build(output_dir=output_dir)

    with zipfile.ZipFile(zip_path) as zf:
        namelist = zf.namelist()

    assert namelist == EXPECTED_FILES
