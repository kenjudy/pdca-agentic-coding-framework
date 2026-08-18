#!/bin/bash
# Build script for PDCA Framework Claude Skill
#
# Thin wrapper over build.py — the single shared implementation of the build
# (issue #114). No build logic lives here: what gets built, how files are
# assembled, license stripping, injection processing, and packaging are all
# in build.py so build-skill.sh and build-skill.ps1 cannot drift apart.
#
# Uses python3 rather than `uv run python3`: build.py has no third-party
# dependencies (stdlib only — sys, zipfile, pathlib), so a bare python3 is
# enough to build the package standalone, without requiring uv or a synced
# venv. `uv run` is for the test suite, which does have dependencies.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/build.py"
