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
echo "=== Checking plugin skill copy is fresh (#203) ==="
# build.py just wrote the plugin's embedded skill directory from the masters. If
# that differs from what is committed, a master or SKILL.md changed without the
# plugin's embedded copy being regenerated and committed alongside it -- catch it
# here, not after a marketplace install ships stale content.
#
# The path is derived from build.PLUGIN_SKILL_DIR, never hardcoded: a literal
# string here would silently stop protecting anything the moment the plugin
# directory is renamed (git status --porcelain on a missing path exits 0 with
# empty output, not a loud failure).
#
# `git status --porcelain`, not `git diff --exit-code`: diff only sees changes to
# already-tracked files, so it is blind to a reference file added to MANIFEST
# without `git add` (build.py prunes removed ones, but a newly-added file still
# needs staging). Porcelain output includes untracked ("??") entries too.
PLUGIN_SKILL_DIR="$(cd "$SCRIPT_DIR" && uv run --locked python3 -c 'import build; print(build.PLUGIN_SKILL_DIR)')"

# Trust nothing about the derived path: an empty value or a missing directory
# must abort loudly, not fall through into a `git status` call whose failure
# (or vacuous success) would silently read as "nothing to report" -- exactly
# the fail-open failure mode this whole gate exists to avoid.
if [ -z "$PLUGIN_SKILL_DIR" ] || [ ! -d "$SCRIPT_DIR/../$PLUGIN_SKILL_DIR" ]; then
    echo "✗ Could not resolve the plugin skill directory (build.PLUGIN_SKILL_DIR resolved"
    echo "  to '$PLUGIN_SKILL_DIR', which is empty or not a directory) -- aborting rather"
    echo "  than silently skipping the freshness check."
    exit 1
fi

set +e
FRESHNESS_STATUS="$(git -C "$SCRIPT_DIR/.." status --porcelain -- "$PLUGIN_SKILL_DIR")"
GIT_STATUS_EXIT=$?
set -e
if [ "$GIT_STATUS_EXIT" -ne 0 ]; then
    echo "✗ 'git status' failed while checking $PLUGIN_SKILL_DIR (exit $GIT_STATUS_EXIT) --"
    echo "  aborting rather than treating an error as 'nothing to report'."
    exit 1
fi
if [ -n "$FRESHNESS_STATUS" ]; then
    FRESHNESS_EXIT=1
    echo "✗ $PLUGIN_SKILL_DIR is stale -- run 'bash build-skill.sh'"
    echo "  and commit the result alongside the master/SKILL.md change above."
    echo "$FRESHNESS_STATUS"
else
    FRESHNESS_EXIT=0
fi

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
COMBINED_EXIT=$(( FRESHNESS_EXIT > COMBINED_EXIT ? FRESHNESS_EXIT : COMBINED_EXIT ))

if [ "$COMBINED_EXIT" -eq 0 ]; then
    echo ""
    echo "✓ All checks passed."
    exit 0
else
    echo ""
    echo "✗ Checks failed (freshness=$FRESHNESS_EXIT ruff=$RUFF_EXIT tests=$TEST_EXIT)."
    if [ "$WARN_ONLY" = "1" ]; then
        echo "  (warn-only mode — commit allowed)"
        exit 0
    else
        exit "$COMBINED_EXIT"
    fi
fi
