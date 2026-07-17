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

echo "=== Running PDCA Prompt Evaluations ==="
echo "Judge model: claude-haiku-4-5-20251001"
echo ""

if [ $# -gt 0 ]; then
  (cd "$SCRIPT_DIR" && uv run python -m pytest -m eval -v "$@")
else
  (cd "$SCRIPT_DIR" && uv run python -m pytest tests/test_evals.py -m eval -v)
fi
