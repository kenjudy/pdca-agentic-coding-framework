#!/usr/bin/env bash
# run-evals.sh — Run LLM-as-judge evaluation tests against PDCA phase prompts.
#
# Requires ANTHROPIC_API_KEY in environment (or .env file).
# Uses Claude Haiku as the judge model — costs approximately $2-5 per full run.
# Never runs automatically on push or pull_request. evals.yml DOES invoke this script,
# but only via workflow_dispatch -- a human-triggered run, not an automatic one (#159).
#
# Usage:
#   bash run-evals.sh                     # run all eval tests
#   bash run-evals.sh tests/test_evals.py::TestPrompt1aEvals  # run one class

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The harness reads the BUILT prompt files under pdca-framework/references/, which
# are gitignored artifacts. Without these two lines every scenario dies with
# FileNotFoundError on do-prompts.md before reaching the API -- and each shot is then
# reported as "did not pass", which in a summary count is indistinguishable from the
# model actually failing the scenario. A harness that cannot run must not read like a
# harness delivering a verdict. (Same shape as issue #89, in the script next door.)
echo "=== Syncing eval dependencies ==="
(cd "$SCRIPT_DIR" && uv sync --locked --extra test --extra eval)

echo ""
echo "=== Building PDCA Framework Skill ==="
bash "$SCRIPT_DIR/build-skill.sh"

echo ""
echo "=== Running PDCA Prompt Evaluations ==="
echo "Judge model: claude-haiku-4-5-20251001"
echo ""

# Marker for "reports written by THIS run". eval/results/ accumulates across runs,
# so checking the whole directory would let an earlier scored report mask a run that
# scored nothing -- the stale-artifact hazard BUILD.md documents for the build.
MARKER="$(mktemp)"
trap 'rm -f "$MARKER"' EXIT

set +e
if [ $# -gt 0 ]; then
  (cd "$SCRIPT_DIR" && uv run python -m pytest -m eval -v "$@")
else
  (cd "$SCRIPT_DIR" && uv run python -m pytest tests/test_evals.py -m eval -v)
fi
PYTEST_EXIT=$?
set -e

# A shot that dies before reaching the API produces no scored result, but pytest
# exits non-zero either way -- so a caller counting exit codes reports a crash and a
# real scenario failure identically. That is how "5 shot(s); 5 did not pass" was
# reported for a harness that never called the API once (#131 Step 0). Distinguish
# them here, where the reports are, rather than leaving every caller to guess.
NEW_REPORTS=$(find "$SCRIPT_DIR/eval/results" -name '*.md' -newer "$MARKER" 2>/dev/null || true)

echo ""
if [ -z "$NEW_REPORTS" ]; then
  echo "=== Harness check ==="
  echo "✗ This run wrote no report at all. Nothing was measured." >&2
  echo "  Do not read the exit code below as a scenario verdict." >&2
  exit 2
fi

echo "=== Harness check ==="
# shellcheck disable=SC2086
if ! (cd "$SCRIPT_DIR" && python3 check_eval_ran.py $NEW_REPORTS); then
  echo "  Exit code 2 means the harness did not run -- distinct from 1, a scenario failure." >&2
  exit 2
fi

# Promotion into eval/baselines/ has been entirely manual since #152 created the
# directory, prompted by nothing, so every full sweep since has been read once and
# discarded (#157 has had nothing to pool over as a direct result). promote_baseline.py
# decides on its own whether this was a full sweep -- by checking whether the report
# covers every scenario, not by trusting that this script was invoked with no arguments
# -- and never blocks when stdin is not a terminal, which is how evals.yml calls this
# script in CI. A single new report is expected per invocation: the reporter's
# write_report fixture is session-scoped, firing once at teardown.
for report in $NEW_REPORTS; do
  python3 "$SCRIPT_DIR/promote_baseline.py" "$report"
done

exit "$PYTEST_EXIT"
