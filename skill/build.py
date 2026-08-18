"""Shared builder for the pdca-framework skill package.

Single source of truth for the build. `build-skill.sh` and `build-skill.ps1` are
thin wrappers that call `build()` — neither carries build logic of its own, so the
two platforms cannot drift apart (issue #114).

Every path derives from `skill_dir`, the directory holding this file, mirroring
the way `build-skill.sh` derived everything from `SCRIPT_DIR`:

    skill_dir ─┬─ repo_root  = skill_dir/..                   the Obsidian masters
               ├─ core_dir   = skill_dir/pdca-framework       SKILL.md, addon sources,
               │                                              and the generated references/
               └─ skill_file = skill_dir/pdca-framework.skill the packaged zip
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

SKILL_NAME = "pdca-framework"

# sed '/^## License & Attribution/,$ d' — the built prompt files omit the attribution
# block, which is meaningful to a human reading the repo but costs ~760 tokens of
# in-context overhead with no value to Claude.
LICENSE_HEADING = "## License & Attribution"

PLAN_HEADER = """# PLAN Phase: Analysis & Detailed Planning

This file contains prompts for both analysis (1a) and planning (1b) phases.

---

"""

# Masters live at the repo root, outside core_dir.
MASTER_1A = "1. Plan/1a Analyze to determine approach for achieving the goal.md"
MASTER_1B = "1. Plan/1b Create a detailed implementation plan.md"
MASTER_DO = "2. Do/2. Test Drive the Change.md"
MASTER_ANTI_PATTERNS = "2. Do/Testing Anti-Patterns.md"
MASTER_CHECK = "3. Check/3. Completeness Check.md"
MASTER_ACT = "4. Act/4. Retrospect for continuous improvement.md"
MASTER_WORKING_AGREEMENTS = "Human Working Agreements.md"

# Built by stripping the license block from a single master.
STRIPPED_FROM_MASTER = {
    "do-prompts.md": MASTER_DO,
    "check-prompts.md": MASTER_CHECK,
    "act-prompts.md": MASTER_ACT,
    "working-agreements.md": MASTER_WORKING_AGREEMENTS,
}

# Copied verbatim — deliberately NOT license-stripped. testing-anti-patterns.md
# carries no attribution block to strip, and the addon sources keep theirs
# (beads-setup.md's is intentional). Normalising these would silently change the
# shipped package without failing a test.
COPIED_FROM_MASTER = {
    "testing-anti-patterns.md": MASTER_ANTI_PATTERNS,
}

COPIED_FROM_ADDON = {
    "plan-beads-addon.md": "beads-addon/sources/plan-beads-addon.md",
    "do-beads-addon.md": "beads-addon/sources/do-beads-addon.md",
    "check-beads-addon.md": "beads-addon/sources/check-beads-addon.md",
    "act-beads-addon.md": "beads-addon/sources/act-beads-addon.md",
    "beads-setup.md": "beads-addon/sources/beads-setup.md",
    "beads-workflow.md": "beads-addon/sources/beads-workflow.md",
    "ponytail-setup.md": "ponytail-addon/sources/ponytail-setup.md",
    "ponytail-workflow.md": "ponytail-addon/sources/ponytail-workflow.md",
}

EXPORT_SCRIPT_SRC = "beads-addon/scripts/export-requirements.sh"
EXPORT_SCRIPT_DEST = "scripts/export-requirements.sh"

# The only manifest member that must carry a non-default zip permission. Set as
# a literal, never derived from the on-disk mode: build.py writes every file
# with write_text(), which truncates an existing file in place and leaves its
# mode untouched, so a build that follows a bash-built tree would otherwise
# silently inherit whatever chmod that run left behind (see "Stale-artifact
# masking" in BUILD.md). A literal keeps the package deterministic regardless
# of build history.
EXECUTABLE_MEMBER = f"references/{EXPORT_SCRIPT_DEST}"
EXECUTABLE_MODE = 0o755

# Injections are applied only to the four phase prompt files.
INJECTED_FILES = (
    "plan-prompts.md",
    "do-prompts.md",
    "check-prompts.md",
    "act-prompts.md",
)

# Explicit rather than globbed: a file that is built but not listed here must fail
# the manifest test rather than ship by accident, and a file listed but not built
# must fail the build. This is the single list that drives both the package and
# the ordering — the omission that made the PowerShell script ship 7 of 16 files
# is not expressible here.
MANIFEST = (
    "SKILL.md",
    "references/plan-prompts.md",
    "references/do-prompts.md",
    "references/check-prompts.md",
    "references/act-prompts.md",
    "references/working-agreements.md",
    "references/plan-beads-addon.md",
    "references/do-beads-addon.md",
    "references/check-beads-addon.md",
    "references/act-beads-addon.md",
    "references/beads-setup.md",
    "references/beads-workflow.md",
    "references/ponytail-setup.md",
    "references/ponytail-workflow.md",
    "references/testing-anti-patterns.md",
    f"references/{EXPORT_SCRIPT_DEST}",
)


class BuildError(Exception):
    """A required source file is missing, or the package could not be assembled."""


def strip_license(text: str) -> str:
    """Drop the attribution block: everything from its heading to end of file.

    Mirrors `sed '/^## License & Attribution/,$ d'` — anchored at line start, first
    match wins, and text without the heading passes through untouched.
    """
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(LICENSE_HEADING):
            return "".join(lines[:index])
    return text


def apply_injections(text: str, injections_dir: Path) -> str:
    """Replace `<!-- CLAUDE_INJECT: key -->` markers with their injection content.

    The key is the injection file's stem. Markers are HTML comments so they stay
    invisible in Obsidian; an unreplaced marker is a defect that ships raw into the
    agent's context.
    """
    for injection in sorted(injections_dir.glob("*.md")):
        marker = f"<!-- CLAUDE_INJECT: {injection.stem} -->"
        text = text.replace(marker, injection.read_text().rstrip("\n"))
    return text


def _read(path: Path) -> str:
    if not path.is_file():
        raise BuildError(f"Required source file not found: {path}")
    return path.read_text()


def build(skill_dir: Path) -> Path:
    """Build the skill package. Returns the path to the written .skill zip."""
    skill_dir = Path(skill_dir).resolve()
    repo_root = skill_dir.parent
    core_dir = skill_dir / SKILL_NAME
    references = core_dir / "references"
    injections_dir = core_dir / "claude-addon" / "injections"
    skill_file = skill_dir / f"{SKILL_NAME}.skill"

    if not (core_dir / "SKILL.md").is_file():
        raise BuildError(f"Skill descriptor not found: {core_dir / 'SKILL.md'}")
    if not injections_dir.is_dir():
        raise BuildError(f"Claude injections directory not found: {injections_dir}")

    references.mkdir(parents=True, exist_ok=True)
    (references / "scripts").mkdir(exist_ok=True)

    # plan-prompts.md is a concatenation of two masters, not a copy.
    (references / "plan-prompts.md").write_text(
        PLAN_HEADER
        + strip_license(_read(repo_root / MASTER_1A))
        + "\n---\n\n"
        + strip_license(_read(repo_root / MASTER_1B))
    )

    for name, master in STRIPPED_FROM_MASTER.items():
        (references / name).write_text(strip_license(_read(repo_root / master)))

    for name, master in COPIED_FROM_MASTER.items():
        (references / name).write_text(_read(repo_root / master))

    for name in INJECTED_FILES:
        target = references / name
        target.write_text(apply_injections(target.read_text(), injections_dir))

    for name, addon_source in COPIED_FROM_ADDON.items():
        (references / name).write_text(_read(core_dir / addon_source))

    (references / EXPORT_SCRIPT_DEST).write_text(_read(core_dir / EXPORT_SCRIPT_SRC))

    skill_file.unlink(missing_ok=True)
    with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as archive:
        for member in MANIFEST:
            member_path = core_dir / member
            if not member_path.is_file():
                raise BuildError(f"Manifest lists a file the build did not produce: {member_path}")
            arcname = f"{SKILL_NAME}/{member}"
            if member == EXECUTABLE_MEMBER:
                # ZipFile.write() derives external_attr from the file's on-disk
                # mode, which is exactly the non-determinism described above.
                # Build the ZipInfo by hand so the permission bit is a literal.
                info = zipfile.ZipInfo.from_file(member_path, arcname=arcname)
                info.external_attr = EXECUTABLE_MODE << 16
                info.compress_type = archive.compression
                archive.writestr(info, member_path.read_bytes())
            else:
                archive.write(member_path, arcname=arcname)

    return skill_file


def main() -> int:
    try:
        skill_file = build(Path(__file__).parent)
    except BuildError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Built {skill_file} ({skill_file.stat().st_size} bytes, {len(MANIFEST)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
