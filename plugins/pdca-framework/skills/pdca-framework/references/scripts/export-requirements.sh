#!/usr/bin/env bash
# export-requirements.sh
# Generate a structured requirements document from all open beads epics and their tasks.
#
# Usage:
#   bash export-requirements.sh                  # writes requirements.md in current dir
#   bash export-requirements.sh output.md        # writes to specified path
#
# Scope: all open epics in the local .beads/ database, with all child tasks
# (open or closed) listed under each epic.

set -euo pipefail

OUTPUT="${1:-requirements.md}"
DATE=$(date +%Y-%m-%d)

echo "Generating requirements document..."

{
echo "# Requirements"
echo ""
echo "_Generated: ${DATE}_"
echo ""
echo "---"
echo ""
echo "## Dependency Graph"
echo ""
echo '```'
bd graph --all --compact 2>/dev/null || echo "(no issues or bd not available)"
echo '```'
echo ""
echo "---"
echo ""

# Get all open epics as JSON (one object per line)
EPIC_IDS=$(bd list --type epic --status open --json --limit 0 2>/dev/null \
  | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            d = json.loads(line)
            print(d.get('id', ''))
        except json.JSONDecodeError:
            pass
" 2>/dev/null)

if [ -z "$EPIC_IDS" ]; then
    echo "_No open epics found._"
else
    for EPIC_ID in $EPIC_IDS; do
        [ -z "$EPIC_ID" ] && continue

        echo "## Epic: ${EPIC_ID}"
        echo ""
        bd show "$EPIC_ID" 2>/dev/null || echo "_Could not load epic ${EPIC_ID}_"
        echo ""
        echo "### Tasks"
        echo ""

        # All child tasks whether open or closed
        TASK_IDS=$(bd list --parent "$EPIC_ID" --all --json --limit 0 2>/dev/null \
          | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            d = json.loads(line)
            print(d.get('id', ''))
        except json.JSONDecodeError:
            pass
" 2>/dev/null)

        if [ -z "$TASK_IDS" ]; then
            echo "_No tasks found for ${EPIC_ID}._"
        else
            for TASK_ID in $TASK_IDS; do
                [ -z "$TASK_ID" ] && continue
                echo "#### ${TASK_ID}"
                echo ""
                bd show "$TASK_ID" 2>/dev/null || echo "_Could not load task ${TASK_ID}_"
                echo ""
            done
        fi

        echo "---"
        echo ""
    done
fi
} > "$OUTPUT"

echo "Requirements document written to: $OUTPUT"
