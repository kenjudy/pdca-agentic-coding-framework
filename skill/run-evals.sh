#!/usr/bin/env bash
# run-evals.sh — Run LLM-as-judge evaluation tests against PDCA phase prompts.
#
# Requires ANTHROPIC_API_KEY in environment (or .env file).
# Uses Claude Haiku as the judge model — costs approximately $2-5 per full run.
# NOT run in CI — invoke manually when iterating on phase prompt quality.
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

if [ $# -gt 0 ]; then
  (cd "$SCRIPT_DIR" && uv run python -m pytest -m eval -v "$@")
else
  (cd "$SCRIPT_DIR" && uv run python -m pytest tests/test_evals.py -m eval -v)
fi
