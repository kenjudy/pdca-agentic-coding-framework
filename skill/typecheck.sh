#!/usr/bin/env bash
# Single source of truth for what mypy checks.
#
# CI and the pre-commit hook in .claude/settings.json both call this. They
# previously carried separate argument lists and had already drifted -- the hook
# named `eval tests/test_build.py` while CI named six targets -- which is #114 in
# miniature: two copies of one procedure diverging silently because only one of
# them ever ran.
#
# tests/test_build.py::test_ci_mypy_covers_every_top_level_module asserts that every
# top-level module under skill/ appears below, so coverage cannot quietly fail to
# grow with the code. build.py went unchecked until #126 and check_changelog.py was
# never added at all until #141 -- both the same slip.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"
exec uv run --locked mypy \
  eval \
  tests \
  build.py \
  check_changelog.py \
  check_eval_ran.py \
  check_release_version.py \
  promote_baseline.py \
  "$@"
