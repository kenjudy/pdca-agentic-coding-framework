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

from test_build import CLAUDE_SKILL_DIR, EXPECTED_FILES, SKILL_FILE, SKILL_NAME


def test_builder_produces_expected_manifest():
    import build

    zip_path = build.build(skill_dir=CLAUDE_SKILL_DIR)

    assert zip_path == SKILL_FILE

    with zipfile.ZipFile(zip_path) as zf:
        namelist = zf.namelist()

    assert sorted(namelist) == sorted(EXPECTED_FILES)


def test_export_script_is_executable():
    """The packaged export-requirements.sh must retain the owner-execute bit.

    Python's zipfile drops permissions unless external_attr is set explicitly
    on the ZipInfo member (see "Behavior build.py must reproduce exactly" in
    BUILD-EXTRACTION-PLAN.md). The bash build produces 0o755 for this member
    (Step 0 baseline); build.py does not yet set external_attr, so this is
    expected to fail until Step 4.

    The generated file is removed first so the assertion reflects build.py's
    own permission handling rather than inheriting the mode of a stale file
    left behind by a prior build (build.py writes via write_text(), which
    truncates an existing file in place and leaves its mode untouched --
    that would let a leftover 0o755 from an earlier bash-script run silently
    make this test pass without build.py ever setting external_attr).
    """
    import build

    generated_script = CLAUDE_SKILL_DIR / SKILL_NAME / "references" / "scripts" / "export-requirements.sh"
    generated_script.unlink(missing_ok=True)

    zip_path = build.build(skill_dir=CLAUDE_SKILL_DIR)
    member = f"{SKILL_NAME}/references/scripts/export-requirements.sh"

    with zipfile.ZipFile(zip_path) as zf:
        info = zf.getinfo(member)

    mode = (info.external_attr >> 16) & 0o777
    assert mode == 0o755, (
        f"{member} has mode {oct(mode)} in the package, expected 0o755 "
        "(owner-execute bit) -- zipfile dropped the permission bit because "
        "build.py does not set external_attr on this member"
    )
