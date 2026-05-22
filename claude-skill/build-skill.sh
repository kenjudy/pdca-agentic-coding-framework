#!/bin/bash
# Build script for PDCA Framework Claude Skill
# Generates ONE unified skill package: pdca-framework.skill
# Includes base prompt files + optional beads addon files (progressive disclosure)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Building PDCA Framework Skill (Unified Package)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_DIR="$SCRIPT_DIR/pdca-framework"
BEADS_DIR="$CORE_DIR/beads-addon"

# Master source files (Obsidian notes — source of truth for prompt content)
MASTER_1A="$REPO_ROOT/1. Plan/1a Analyze to determine approach for achieving the goal.md"
MASTER_1B="$REPO_ROOT/1. Plan/1b Create a detailed implementation plan.md"
MASTER_2="$REPO_ROOT/2. Do/2. Test Drive the Change.md"
MASTER_ANTI_PATTERNS="$REPO_ROOT/2. Do/Testing Anti-Patterns.md"
MASTER_3="$REPO_ROOT/3. Check/3. Completeness Check.md"
MASTER_4="$REPO_ROOT/4. Act/4. Retrospect for continuous improvement.md"
MASTER_WORKING_AGREEMENTS="$REPO_ROOT/Human Working Agreements.md"

# Claude addon injection files (source — NOT build artifacts)
CLAUDE_ADDON_DIR="$CORE_DIR/claude-addon/injections"

# Beads addon files (source — NOT build artifacts)
BEADS_PLAN_ADDON="$BEADS_DIR/sources/plan-beads-addon.md"
BEADS_DO_ADDON="$BEADS_DIR/sources/do-beads-addon.md"
BEADS_CHECK_ADDON="$BEADS_DIR/sources/check-beads-addon.md"
BEADS_ACT_ADDON="$BEADS_DIR/sources/act-beads-addon.md"
BEADS_SETUP="$BEADS_DIR/sources/beads-setup.md"
BEADS_WORKFLOW="$BEADS_DIR/sources/beads-workflow.md"
BEADS_EXPORT_SCRIPT="$BEADS_DIR/scripts/export-requirements.sh"

# Verify master files exist
echo -e "${BLUE}Verifying master source files...${NC}"
for file in "$MASTER_1A" "$MASTER_1B" "$MASTER_2" "$MASTER_ANTI_PATTERNS" "$MASTER_3" "$MASTER_4" "$MASTER_WORKING_AGREEMENTS"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Master file not found: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All master files found${NC}\n"

# Verify Claude addon injection files exist
echo -e "${BLUE}Verifying Claude addon injection files...${NC}"
CLAUDE_INJECTION_FILES=("goal-probe.md" "plan-mode-probe.md" "think-probe.md" "do-think-probe.md" "check-review-probe.md" "act-retro-probes.md")
for fname in "${CLAUDE_INJECTION_FILES[@]}"; do
    if [ ! -f "$CLAUDE_ADDON_DIR/$fname" ]; then
        echo -e "${RED}Error: Claude injection file not found: $CLAUDE_ADDON_DIR/$fname${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All Claude injection files found${NC}\n"

# Verify beads addon files exist
echo -e "${BLUE}Verifying beads addon files...${NC}"
for file in "$BEADS_PLAN_ADDON" "$BEADS_DO_ADDON" "$BEADS_CHECK_ADDON" "$BEADS_ACT_ADDON" "$BEADS_SETUP" "$BEADS_WORKFLOW" "$BEADS_EXPORT_SCRIPT"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Beads addon file not found: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All beads addon files found${NC}\n"

# Create build directory
mkdir -p "$CORE_DIR/references"

# Replace <!-- CLAUDE_INJECT: key --> markers in a built reference file with the
# corresponding injection content from claude-addon/injections/<key>.md.
# Markers are HTML comments — invisible in Obsidian, replaced at build time.
process_injections() {
    local file="$1"
    for injection_file in "$CLAUDE_ADDON_DIR"/*.md; do
        local key
        key=$(basename "$injection_file" .md)
        python3 - "$file" "$injection_file" "$key" << 'PYEOF'
import sys
target_file, inject_file, key = sys.argv[1], sys.argv[2], sys.argv[3]
marker = f"<!-- CLAUDE_INJECT: {key} -->"
with open(inject_file, "r") as f:
    content = f.read().rstrip("\n")
with open(target_file, "r") as f:
    text = f.read()
text = text.replace(marker, content)
with open(target_file, "w") as f:
    f.write(text)
PYEOF
    done
}

# Strip license block from a file — removes "## License & Attribution" to EOF.
# Source templates retain the block for GitHub/documentation; built files omit it
# since the attribution text has no value to Claude in-context.
strip_license() {
    sed '/^## License & Attribution/,$ d' "$1"
}

# ═══════════════════════════════════════════════════════
# BUILD BASE PROMPT FILES (from Obsidian masters)
# ═══════════════════════════════════════════════════════

echo -e "${YELLOW}┌─────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  Building base prompt files from masters            │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────┘${NC}\n"

# plan-prompts.md combines 1a and 1b masters (license stripped from both)
echo -e "${BLUE}Building plan-prompts.md...${NC}"
cat > "$CORE_DIR/references/plan-prompts.md" << 'EOF'
# PLAN Phase: Analysis & Detailed Planning

This file contains prompts for both analysis (1a) and planning (1b) phases.

---

EOF
strip_license "$MASTER_1A" >> "$CORE_DIR/references/plan-prompts.md"
echo -e "\n---\n" >> "$CORE_DIR/references/plan-prompts.md"
strip_license "$MASTER_1B" >> "$CORE_DIR/references/plan-prompts.md"
echo -e "${GREEN}✓ Built plan-prompts.md${NC}"

echo -e "${BLUE}Building do-prompts.md...${NC}"
strip_license "$MASTER_2" > "$CORE_DIR/references/do-prompts.md"
echo -e "${GREEN}✓ Built do-prompts.md${NC}"

echo -e "${BLUE}Building testing-anti-patterns.md...${NC}"
cp "$MASTER_ANTI_PATTERNS" "$CORE_DIR/references/testing-anti-patterns.md"
echo -e "${GREEN}✓ Built testing-anti-patterns.md${NC}"

echo -e "${BLUE}Building check-prompts.md...${NC}"
strip_license "$MASTER_3" > "$CORE_DIR/references/check-prompts.md"
echo -e "${GREEN}✓ Built check-prompts.md${NC}"

echo -e "${BLUE}Building act-prompts.md...${NC}"
strip_license "$MASTER_4" > "$CORE_DIR/references/act-prompts.md"
echo -e "${GREEN}✓ Built act-prompts.md${NC}"

echo -e "${BLUE}Building working-agreements.md...${NC}"
strip_license "$MASTER_WORKING_AGREEMENTS" > "$CORE_DIR/references/working-agreements.md"
echo -e "${GREEN}✓ Built working-agreements.md${NC}\n"

# ═══════════════════════════════════════════════════════
# INJECT CLAUDE-SPECIFIC CONTENT
# ═══════════════════════════════════════════════════════

echo -e "${YELLOW}┌─────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  Injecting Claude-specific content                  │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────┘${NC}\n"

process_injections "$CORE_DIR/references/plan-prompts.md"
process_injections "$CORE_DIR/references/do-prompts.md"
process_injections "$CORE_DIR/references/check-prompts.md"
process_injections "$CORE_DIR/references/act-prompts.md"
echo -e "${GREEN}✓ Claude-specific injections applied${NC}\n"

# ═══════════════════════════════════════════════════════
# COPY BEADS ADDON FILES (progressive disclosure references)
# ═══════════════════════════════════════════════════════

echo -e "${YELLOW}┌─────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  Copying beads addon files                          │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────┘${NC}\n"

cp "$BEADS_PLAN_ADDON"  "$CORE_DIR/references/plan-beads-addon.md"
cp "$BEADS_DO_ADDON"    "$CORE_DIR/references/do-beads-addon.md"
cp "$BEADS_CHECK_ADDON" "$CORE_DIR/references/check-beads-addon.md"
cp "$BEADS_ACT_ADDON"   "$CORE_DIR/references/act-beads-addon.md"
cp "$BEADS_SETUP"       "$CORE_DIR/references/beads-setup.md"
cp "$BEADS_WORKFLOW"    "$CORE_DIR/references/beads-workflow.md"
mkdir -p "$CORE_DIR/references/scripts"
cp "$BEADS_EXPORT_SCRIPT" "$CORE_DIR/references/scripts/export-requirements.sh"
chmod +x "$CORE_DIR/references/scripts/export-requirements.sh"
echo -e "${GREEN}✓ Copied 6 beads addon files + 1 script${NC}\n"

# ═══════════════════════════════════════════════════════
# PACKAGE UNIFIED SKILL
# ═══════════════════════════════════════════════════════

if [ ! -f "$CORE_DIR/SKILL.md" ]; then
    echo -e "${RED}Error: core/SKILL.md not found${NC}"
    exit 1
fi

echo -e "${BLUE}Creating pdca-framework.skill package...${NC}"
# Marketplace requirement: ZIP root folder must match the skill name.
SKILL_FILE="$SCRIPT_DIR/pdca-framework.skill"
[ -f "$SKILL_FILE" ] && rm "$SKILL_FILE"

cd "$SCRIPT_DIR"
zip -r "$SKILL_FILE" \
    pdca-framework/SKILL.md \
    pdca-framework/references/plan-prompts.md \
    pdca-framework/references/do-prompts.md \
    pdca-framework/references/check-prompts.md \
    pdca-framework/references/act-prompts.md \
    pdca-framework/references/working-agreements.md \
    pdca-framework/references/plan-beads-addon.md \
    pdca-framework/references/do-beads-addon.md \
    pdca-framework/references/check-beads-addon.md \
    pdca-framework/references/act-beads-addon.md \
    pdca-framework/references/beads-setup.md \
    pdca-framework/references/beads-workflow.md \
    pdca-framework/references/testing-anti-patterns.md \
    pdca-framework/references/scripts/export-requirements.sh \
    -x "*.DS_Store" \
    -q

if [ ! -f "$SKILL_FILE" ]; then
    echo -e "${RED}Error: Failed to create pdca-framework.skill${NC}"
    exit 1
fi

SKILL_SIZE=$(du -h "$SKILL_FILE" | cut -f1)
echo -e "${GREEN}✓ Created pdca-framework.skill ($SKILL_SIZE)${NC}\n"

# ═══════════════════════════════════════════════════════
# BUILD SUMMARY
# ═══════════════════════════════════════════════════════

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Build Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}Unified Package:${NC}"
echo -e "  File: pdca-framework.skill"
echo -e "  Size: $SKILL_SIZE"
unzip -l "$SKILL_FILE"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo "1. Review generated files in pdca-framework/references/"
echo "2. Install: unzip -o pdca-framework.skill -d ~/.claude/skills/pdca-framework/"
echo "3. Commit changes if everything looks good"
echo ""
echo -e "${YELLOW}Per-project beads setup reminder:${NC}"
echo "  Choose a .beads/ sharing strategy (see references/beads-setup.md):"
echo "  Option A (git-native): commit issues.jsonl + interactions.jsonl, exclude embeddeddolt/"
echo "  Option B (Dolt-native): exclude .beads/ from git, share via 'bd dolt push'"
echo ""
