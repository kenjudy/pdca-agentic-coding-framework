"""
Tests for the shared builder extraction (issue #114): build.py, and parity
between build-skill.sh and build-skill.ps1, both thin wrappers over it.

`build.py` exposes the pinned one-parameter interface
`build(skill_dir: Path) -> Path` (see "The build.py interface" under
Architecture in BUILD.md).

The build writes references/ and the .skill zip to gitignored artifacts
that run-tests.sh regenerates every run, so these tests call build() (or
run the wrapper scripts) against the real skill/ directory (CLAUDE_SKILL_DIR
from test_build.py) rather than redirecting into a temp dir -- there is
nothing hermetic to protect. See "Stale-artifact masking" in BUILD.md for
why builds must still force a from-scratch state before any comparison.
"""

import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
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
    on the ZipInfo member (see "Stale-artifact masking" under Architecture in
    BUILD.md, and the EXECUTABLE_MODE handling in build.py). The bash build
    produces 0o755 for this member; build.py reproduces it by setting
    external_attr as a literal rather than deriving it from disk.

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
        "(owner-execute bit) -- the packaged member does not carry the "
        "owner-execute bit that this file must ship with"
    )


def _find_pwsh() -> str | None:
    """Locate a pwsh executable: PATH first (how CI will have it), then the
    fixed path a manual local install lands at when following PowerShell's
    own tarball installation instructions (extract, then chmod +x) rather
    than a package manager."""
    on_path = shutil.which("pwsh")
    if on_path:
        return on_path
    fixed_install = Path("/opt/pwsh/pwsh")
    if fixed_install.is_file():
        return str(fixed_install)
    return None


def _clean_build_artifacts() -> None:
    """Remove every artifact either build script can leave behind, so the
    next build starts from scratch.

    Per "Stale-artifact masking" under Architecture in BUILD.md: build.py
    writes files in place (write_text() truncates an existing file rather
    than recreating it), so leftovers from a previous run -- of either
    script -- can silently survive into the next build and make two
    different builds look identical when they are not. A parity test that
    doesn't force a from-scratch state on both sides of the comparison
    risks exactly the false pass this project already had once.
    """
    references = CLAUDE_SKILL_DIR / SKILL_NAME / "references"
    if references.exists():
        shutil.rmtree(references)
    # build-skill.ps1's stale $SrcDir logic creates skill/src/ -- not
    # gitignored, and not cleaned by any build path.
    stale_src = CLAUDE_SKILL_DIR / "src"
    if stale_src.exists():
        shutil.rmtree(stale_src)
    if SKILL_FILE.exists():
        SKILL_FILE.unlink()


def _manifest(zip_path: Path) -> dict[str, str]:
    """{member name: sha256} for a built package.

    Callers must capture this before triggering the next build -- both
    build-skill.sh and build-skill.ps1 write to the same skill_file path,
    so the zip this reads from will be overwritten by whichever build runs
    next.
    """
    with zipfile.ZipFile(zip_path) as zf:
        return {name: hashlib.sha256(zf.read(name)).hexdigest() for name in zf.namelist()}


def test_powershell_build_matches_bash():
    """build-skill.ps1 and build-skill.sh must produce byte-identical
    packages (same members, same content) -- the parity guarantee this
    whole extraction exists to make structural rather than merely tested.

    build-skill.ps1 was rewritten at Step 7 as a thin wrapper over build.py,
    the same implementation build-skill.sh wraps, so drift between the two
    platforms is now structurally impossible rather than merely detectable.

    Skipping when pwsh is absent is correct locally -- a contributor
    without PowerShell should not be blocked. It is wrong in CI: a skip and
    a pass are indistinguishable in pytest's summary line, so a CI runner
    that silently lacks pwsh would let this test skip forever and put the
    original undetected-drift condition right back in place. Under CI=true
    (set by GitHub Actions), a missing pwsh is a hard failure instead.
    """
    pwsh = _find_pwsh()
    if pwsh is None:
        if os.environ.get("CI") == "true":
            pytest.fail(
                "pwsh not found on PATH or at /opt/pwsh/pwsh, and CI=true -- "
                "skipping here would be the exact blind spot this test exists "
                "to close (a skipped parity test is indistinguishable from a "
                "passing one in the summary line). The CI runner image must "
                "provide pwsh; see .github/workflows/test.yml."
            )
        pytest.skip("pwsh not found on PATH or at /opt/pwsh/pwsh -- cannot verify ps1/bash parity")
    assert pwsh is not None  # narrows for mypy; pytest.skip()/fail() above always raise

    try:
        _clean_build_artifacts()
        bash_result = subprocess.run(
            ["bash", "build-skill.sh"],
            cwd=str(CLAUDE_SKILL_DIR),
            capture_output=True,
            text=True,
        )
        assert bash_result.returncode == 0, (
            f"bash build-skill.sh failed (exit {bash_result.returncode}):\n"
            f"STDOUT:\n{bash_result.stdout}\nSTDERR:\n{bash_result.stderr}"
        )
        bash_manifest = _manifest(SKILL_FILE)

        _clean_build_artifacts()
        ps1_result = subprocess.run(
            [pwsh, "-NoProfile", "-File", "build-skill.ps1"],
            cwd=str(CLAUDE_SKILL_DIR),
            capture_output=True,
            text=True,
        )
        assert ps1_result.returncode == 0, (
            f"build-skill.ps1 failed (exit {ps1_result.returncode}):\n"
            f"STDOUT:\n{ps1_result.stdout}\nSTDERR:\n{ps1_result.stderr}"
        )
        ps1_manifest = _manifest(SKILL_FILE)
    finally:
        _clean_build_artifacts()

    bash_names = set(bash_manifest)
    ps1_names = set(ps1_manifest)

    mismatches = []
    if bash_names != ps1_names:
        only_bash = sorted(bash_names - ps1_names)
        only_ps1 = sorted(ps1_names - bash_names)
        mismatches.append(
            f"namelist differs -- bash build has {len(bash_names)} members, "
            f"ps1 build has {len(ps1_names)}. "
            f"Only in bash build: {only_bash}. "
            f"Only in ps1 build: {only_ps1}."
        )
    else:
        for name in sorted(bash_names):
            if bash_manifest[name] != ps1_manifest[name]:
                mismatches.append(
                    f"{name}: content differs -- bash sha256={bash_manifest[name][:16]} "
                    f"!= ps1 sha256={ps1_manifest[name][:16]}"
                )

    assert not mismatches, "build-skill.ps1 package does not match build-skill.sh package:\n" + "\n".join(
        mismatches
    )
