#!/bin/bash
# Installation script for the PDCA Framework skill
# Installs the unified skill for Claude Code or Codex

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_FILE="$SCRIPT_DIR/pdca-framework.skill"
SKILL_NAME="pdca-framework"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   PDCA Framework Skill Installer${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Validate skill file exists
if [ ! -f "$SKILL_FILE" ]; then
    echo -e "${RED}Error: Skill file not found: $SKILL_FILE${NC}"
    echo "Please run ./build-skill.sh first to create the skill package."
    exit 1
fi

SKILL_SIZE=$(du -h "$SKILL_FILE" | cut -f1)

echo -e "${BLUE}Package:${NC} pdca-framework.skill ($SKILL_SIZE)"
echo ""
echo "Includes:"
echo "  • Core PDCA framework (Plan→Do→Check→Act)"
echo "  • Beads integration files (optional — loaded only if beads is installed)"
echo ""

# Step 1: Select Installation Scope
INSTALL_TYPE="${1:-personal}"

echo -e "${YELLOW}Installation Scope:${NC}"
echo ""
echo "  ${GREEN}personal${NC} / ${GREEN}claude${NC} (default) — ~/.claude/skills/  (all your projects)"
echo "  ${GREEN}project${NC}                     — .claude/skills/     (current project, shared via git)"
echo "  ${GREEN}codex${NC}                       — ~/.agents/skills/   (all your projects)"
echo ""

if [ -z "$1" ]; then
    read -p "Install scope? (personal/project/codex) [personal]: " INSTALL_TYPE
    INSTALL_TYPE=${INSTALL_TYPE:-personal}
fi

# Determine installation directory
case "$INSTALL_TYPE" in
    personal|p|claude)
        INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
        PLATFORM="Claude Code"
        SCOPE="Personal"
        SCOPE_DESC="Available across all your projects"
        ;;
    project|proj)
        INSTALL_DIR="$PWD/.claude/skills/$SKILL_NAME"
        PLATFORM="Claude Code"
        SCOPE="Project"
        SCOPE_DESC="Available in current project, shared via git"
        ;;
    codex|c)
        INSTALL_DIR="$HOME/.agents/skills/$SKILL_NAME"
        PLATFORM="Codex"
        SCOPE="Personal"
        SCOPE_DESC="Available across all your Codex projects"
        ;;
    *)
        echo -e "${RED}Error: Invalid scope: $INSTALL_TYPE${NC}"
        echo "Usage: $0 [personal|project|claude|codex]"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Installing to:${NC} $INSTALL_DIR"
echo -e "${BLUE}Scope:${NC} $SCOPE_DESC"
echo ""

# Check if already installed
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Warning: Skill already installed at $INSTALL_DIR${NC}"
    read -p "Overwrite existing installation? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo -e "${BLUE}Removing existing installation...${NC}"
    rm -rf "$INSTALL_DIR"
fi

# Extract skill package
echo -e "${BLUE}Extracting skill package...${NC}"
mkdir -p "$(dirname "$INSTALL_DIR")"
unzip "$SKILL_FILE" -d "$(dirname "$INSTALL_DIR")"

# Verify installation
if [ ! -f "$INSTALL_DIR/SKILL.md" ]; then
    echo -e "${RED}Error: Installation failed - SKILL.md not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""

# Show installed files
echo -e "${BLUE}Installed files:${NC}"
find "$INSTALL_DIR" -type f | sed "s|$INSTALL_DIR/||" | sort
echo ""

echo -e "${GREEN}Success!${NC} The PDCA framework skill is now available in $PLATFORM."
echo ""

# Scope-specific next steps
if [ "$INSTALL_TYPE" = "project" ] || [ "$INSTALL_TYPE" = "proj" ]; then
    echo -e "${BLUE}Next Steps (project install):${NC}"
    echo "1. Commit the skill to share with your team:"
    echo "   git add .claude/skills/"
    echo "   git commit -m 'Add PDCA framework skill'"
    echo ""
fi

# Optional beads setup
echo -e "${YELLOW}Optional: Beads for cross-session task tracking${NC}"
echo ""
echo "The skill includes beads integration files that activate when beads is installed."
echo "Skip this if you only need single-session PDCA cycles."
echo ""
echo -e "${BLUE}Quick setup:${NC}"
echo "  brew install go icu4c dolt"
echo "  ICU_PATH=\$(brew --prefix icu4c@78)"
echo "  export CGO_CFLAGS=\"-I\${ICU_PATH}/include\""
echo "  export CGO_CXXFLAGS=\"-I\${ICU_PATH}/include\""
echo "  export CGO_LDFLAGS=\"-L\${ICU_PATH}/lib\""
echo "  CGO_ENABLED=1 go install github.com/steveyegge/beads/cmd/bd@latest"
echo ""
echo "For full setup instructions, see references/beads-setup.md inside the installed skill."
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  README: $SCRIPT_DIR/README.md"
echo "  Build:  $SCRIPT_DIR/BUILD.md"
echo ""
echo -e "${BLUE}Uninstall:${NC}"
echo "  rm -rf $INSTALL_DIR"
echo ""
