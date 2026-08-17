#!/usr/bin/env bash
# run-ab-eval.sh — Interleaved A/B comparison of two master-prompt variants.
#
# WHY THIS EXISTS
#   The eval harness is stochastic. Scenarios fail on prompt text nobody changed
#   — one CHECK scenario was measured failing 3 of 18 runs against an unmodified
#   master. A single eval run therefore cannot tell you whether your prompt edit
#   caused a failure. Running the arms sequentially cannot either, because API-side
#   variation drifts over minutes.
#
#   This script alternates control and treatment within each pair, rebuilding the
#   skill between arms, so drift hits both arms equally. It then reports a Fisher
#   exact p-value so the result is read rather than eyeballed.
#
# USAGE
#   bash run-ab-eval.sh \
#     --master "3. Check/3. Completeness Check.md" \
#     --control /path/to/control-variant.md \
#     --treatment /path/to/treatment-variant.md \
#     --test 'tests/test_evals.py::TestPrompt3Evals::test_3_scenario[3-all-complete]' \
#     --pairs 6
#
#   Produce the control variant with:  git show <ref>:'<master path>' > control.md
#
# REQUIRES
#   ANTHROPIC_API_KEY in the environment (or skill/.env).
#
# NOTE
#   The working tree's master file is restored to the treatment variant on exit,
#   including on interrupt. Commit or stash before running.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAIRS=6
MASTER="" ; CONTROL="" ; TREATMENT="" ; TEST_ID=""

while [ $# -gt 0 ]; do
  case "$1" in
    --master)    MASTER="$2"    ; shift 2 ;;
    --control)   CONTROL="$2"   ; shift 2 ;;
    --treatment) TREATMENT="$2" ; shift 2 ;;
    --test)      TEST_ID="$2"   ; shift 2 ;;
    --pairs)     PAIRS="$2"     ; shift 2 ;;
    *) echo "Unknown argument: $1" >&2 ; exit 2 ;;
  esac
done

for required in MASTER CONTROL TREATMENT TEST_ID; do
  if [ -z "${!required}" ]; then
    echo "Missing --${required,,}. See the usage block at the top of this script." >&2
    exit 2
  fi
done

MASTER_PATH="$REPO_ROOT/$MASTER"
[ -f "$MASTER_PATH" ]  || { echo "No such master: $MASTER_PATH" >&2 ; exit 2 ; }
[ -f "$CONTROL" ]      || { echo "No such control variant: $CONTROL" >&2 ; exit 2 ; }
[ -f "$TREATMENT" ]    || { echo "No such treatment variant: $TREATMENT" >&2 ; exit 2 ; }

# Always leave the tree on the treatment variant, even if interrupted.
restore() {
  cp "$TREATMENT" "$MASTER_PATH"
  bash "$SCRIPT_DIR/build-skill.sh" >/dev/null 2>&1
}
trap restore EXIT

run_arm() {
  cp "$1" "$MASTER_PATH"
  bash "$SCRIPT_DIR/build-skill.sh" >/dev/null 2>&1
  (cd "$SCRIPT_DIR" && uv run python -m pytest -m eval -q "$TEST_ID" >/dev/null 2>&1)
  local code=$?
  # pytest: 0 = passed, 1 = a test failed. Anything else means the run never
  # happened — uv could not start, collection error, bad node id. Scoring those
  # as content failures manufactures perfect separation: an arm that cannot run
  # loses every pair and the p-value looks decisive. Abort instead.
  if [ $code -gt 1 ]; then
    echo "" >&2
    echo "ABORT: the eval run did not execute (pytest exit $code)." >&2
    echo "  Arm: $1" >&2
    echo "  This is an infrastructure failure, not a result. Nothing is scored." >&2
    echo "  Re-run manually to see the error:" >&2
    echo "    cd $SCRIPT_DIR && uv run python -m pytest -m eval -q '$TEST_ID'" >&2
    exit 3
  fi
  return $code
}

echo "=== Interleaved A/B: $PAIRS pairs ==="
echo "Master:    $MASTER"
echo "Scenario:  $TEST_ID"
echo ""

a_pass=0 ; a_fail=0 ; b_pass=0 ; b_fail=0
for i in $(seq 1 "$PAIRS"); do
  if run_arm "$CONTROL";   then a_pass=$((a_pass+1)) ; r1=PASS ; else a_fail=$((a_fail+1)) ; r1=FAIL ; fi
  if run_arm "$TREATMENT"; then b_pass=$((b_pass+1)) ; r2=PASS ; else b_fail=$((b_fail+1)) ; r2=FAIL ; fi
  echo "pair $i:  control=$r1   treatment=$r2"
done

echo ""
echo "control:   $a_pass pass / $a_fail fail"
echo "treatment: $b_pass pass / $b_fail fail"

(cd "$SCRIPT_DIR" && uv run python -c "
from eval.abstats import fisher_exact_two_tailed
p = fisher_exact_two_tailed($a_pass, $a_fail, $b_pass, $b_fail)
print(f'\nFisher exact (two-tailed): p = {p:.4f}')
if p < 0.05:
    print('  The arms differ. The prompt change is a plausible cause -- investigate it.')
else:
    print('  The arms are indistinguishable. This run is NOT evidence that the prompt')
    print('  change caused anything. Do not rewrite a line on the strength of it;')
    print('  either collect more pairs or accept the null result.')
")
