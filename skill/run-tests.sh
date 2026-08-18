#!/bin/bash
# Canonical test runner for PDCA Framework Skill
# Builds the skill package, then runs the unit test suite (no API calls).
# Used by: git pre-commit hook (warn-only) and GitHub Actions CI (enforcing).
#
# Exit codes:
#   0 — tests passed (or --warn-only mode)
#   1 — tests failed (default; CI uses this to block merges)
#
# Usage:
#   bash run-tests.sh              # exit 1 on failure (CI mode)
#   WARN_ONLY=1 bash run-tests.sh  # exit 0 always (hook mode)
#
# For LLM eval tests (requires ANTHROPIC_API_KEY, incurs API cost):
#   bash run-evals.sh
#
# Both `uv run` calls below use --locked: plain `uv run` silently re-resolves
# and rewrites uv.lock when it drifts from pyproject.toml's constraints,
# dirtying the contributor's working tree with an unrelated dependency diff
# instead of telling them anything is wrong. --locked fails loudly instead
# ("The lockfile at uv.lock needs to be updated") so drift is caught here,
# not discovered later as a stray diff in someone else's commit.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WARN_ONLY="${WARN_ONLY:-0}"

# Provision the venv this script's own tools live in (issue #89). Without this,
# `uv run` auto-creates a venv containing only the project package -- ruff and
# pytest are in optional extras it does not install. On a fresh clone that fails
# outright; worse, if an ambient ruff exists on PATH, `uv run ruff` silently uses
# it and the lint gate reports green while running a version below the floor
# pyproject.toml declares. CI never caught either, because its workflows sync the
# extras before calling this script -- so the script only ever ran pre-provisioned.
# Syncing here makes it self-contained and identical in both places.
echo "=== Syncing dependencies ==="
(cd "$SCRIPT_DIR" && uv sync --locked --extra test --extra lint)

echo ""
echo "=== Building PDCA Framework Skill ==="
bash "$SCRIPT_DIR/build-skill.sh"

echo ""
echo "=== Lint (ruff) ==="
set +e
(cd "$SCRIPT_DIR" && uv run --locked ruff check .) 2>&1
RUFF_EXIT=$?
set -e

echo ""
echo "=== Running Test Suite ==="
set +e
(cd "$SCRIPT_DIR" && uv run --locked python -m pytest tests/ -v) 2>&1
TEST_EXIT=$?
set -e

COMBINED_EXIT=$(( RUFF_EXIT > TEST_EXIT ? RUFF_EXIT : TEST_EXIT ))

if [ "$COMBINED_EXIT" -eq 0 ]; then
    echo ""
    echo "✓ All checks passed."
    exit 0
else
    echo ""
    echo "✗ Checks failed (ruff=$RUFF_EXIT tests=$TEST_EXIT)."
    if [ "$WARN_ONLY" = "1" ]; then
        echo "  (warn-only mode — commit allowed)"
        exit 0
    else
        exit "$COMBINED_EXIT"
    fi
fi
