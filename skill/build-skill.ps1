# Build script for PDCA Framework Claude Skill (Windows)
#
# Thin wrapper over build.py — the single shared implementation of the build
# (issue #114). No build logic lives here: what gets built, how files are
# assembled, license stripping, injection processing, and packaging are all in
# build.py, so build-skill.ps1 and build-skill.sh cannot drift apart.
#
# This script previously carried its own copy of the build and silently fell out
# of sync: it targeted skill/src, a directory renamed to pdca-framework long ago,
# and shipped 7 of 16 files at the wrong zip root with raw CLAUDE_INJECT markers
# and unstripped license blocks. Nothing detected it because nothing ran it.
# tests/test_builder.py::test_powershell_build_matches_bash now does.

$ErrorActionPreference = "Stop"

# build.py is stdlib-only, so any working interpreter will do — no venv, no uv.
# Candidates are probed with --version rather than trusted on presence alone:
# on Windows, python3.exe and python.exe are often Microsoft Store stubs that
# resolve via Get-Command but are not interpreters.
$python = $null
foreach ($candidate in @("python3", "python")) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if (-not $found) { continue }
    & $found.Source --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $python = $found.Source
        break
    }
}

if (-not $python) {
    # Written straight to stderr rather than via Write-Error: under
    # $ErrorActionPreference = "Stop", Write-Error raises a terminating error
    # that aborts the script before the exit below runs, and the process then
    # reports success. Verified — this branch exited 0 before the change.
    [Console]::Error.WriteLine(
        "Error: No working Python interpreter found. Tried 'python3' and 'python'. " +
        "Install Python 3.11+ and ensure it is on PATH.")
    exit 1
}

& $python (Join-Path $PSScriptRoot "build.py")

# A native command's non-zero exit does NOT throw, even under
# $ErrorActionPreference = "Stop" — that governs cmdlets, not external
# processes. Without this explicit propagation the wrapper would report success
# for every failed build.
exit $LASTEXITCODE
