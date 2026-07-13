# Installation script for the PDCA Framework skill (PowerShell)
# Installs the skill for Claude Code or Codex on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("personal", "p", "claude", "codex", "c", "project", "proj")]
    [string]$InstallType
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($InstallType)) {
    Write-Host "Installation Scope:" -ForegroundColor Cyan
    Write-Host "  personal / claude (default) - ~/.claude\skills\ (all your projects)"
    Write-Host "  project                    - .claude\skills\  (current project, shared via git)"
    Write-Host "  codex                      - ~/.agents\skills\  (all your projects)"
    $InstallType = Read-Host "Install scope? (personal/project/codex) [personal]"
    if ([string]::IsNullOrWhiteSpace($InstallType)) {
        $InstallType = "personal"
    }
}

Write-Host "`nPDCA Framework Skill Installer" -ForegroundColor Cyan
Write-Host ""

# Get script directory and skill file path
$ScriptDir = $PSScriptRoot
$SkillFile = Join-Path $ScriptDir "pdca-framework.skill"

# Validate skill file exists
if (-not (Test-Path $SkillFile)) {
    Write-Host "Error: Skill file not found: $SkillFile" -ForegroundColor Red
    Write-Host "Please run build-skill.ps1 first to create the skill package." -ForegroundColor Yellow
    exit 1
}

# Determine installation directory
if ($InstallType -in "personal", "p", "claude") {
    $InstallDir = Join-Path $env:USERPROFILE ".claude\skills\pdca-framework"
    $Platform = "Claude Code"
    $Scope = "Personal (available across all projects)"
} elseif ($InstallType -in "codex", "c") {
    $InstallDir = Join-Path $env:USERPROFILE ".agents\skills\pdca-framework"
    $Platform = "Codex"
    $Scope = "Personal (available across all Codex projects)"
} elseif ($InstallType -in "project", "proj") {
    $InstallDir = Join-Path (Get-Location) ".claude\skills\pdca-framework"
    $Platform = "Claude Code"
    $Scope = "Project (available in current project only)"
} else {
    Write-Host "Error: Invalid scope: $InstallType" -ForegroundColor Red
    Write-Host "Usage: .\install-skill.ps1 [personal|project|claude|codex]" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installation Type: $Scope" -ForegroundColor Cyan
Write-Host "Installation Path: $InstallDir" -ForegroundColor Cyan
Write-Host ""

# Check if already installed
if (Test-Path $InstallDir) {
    Write-Host "Warning: Skill already installed at $InstallDir" -ForegroundColor Yellow
    $response = Read-Host "Overwrite existing installation? (y/N)"
    if ($response -notmatch "^[Yy]$") {
        Write-Host "Installation cancelled."
        exit 0
    }
    Write-Host "Removing existing installation..." -ForegroundColor Cyan
    Remove-Item -Path $InstallDir -Recurse -Force
}

# Create installation directory
Write-Host "Creating installation directory..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Extract skill package
Write-Host "Extracting skill package..." -ForegroundColor Cyan
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($SkillFile, $InstallDir)
} catch {
    Write-Host "Error: Failed to extract skill package" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Verify installation
if (-not (Test-Path (Join-Path $InstallDir "SKILL.md"))) {
    Write-Host "Error: Installation failed - SKILL.md not found" -ForegroundColor Red
    exit 1
}

Write-Host "`nInstallation complete!" -ForegroundColor Green
Write-Host ""

# Show installed files
Write-Host "Installed files:" -ForegroundColor Cyan
Get-ChildItem -Path $InstallDir -Recurse -File | ForEach-Object {
    $relativePath = $_.FullName.Replace($InstallDir, "")
    Write-Host "  $relativePath"
}

Write-Host ""
Write-Host "Success! The PDCA framework skill is now available in $Platform." -ForegroundColor Green
Write-Host ""

# Next steps
Write-Host "Next Steps:" -ForegroundColor Cyan
if ($Platform -eq "Codex") {
    Write-Host "1. The skill is automatically discovered by Codex"
    Write-Host "2. Start a coding session: codex"
    Write-Host "3. Codex will use the skill when appropriate"
    Write-Host ""
    Write-Host "Test it:" -ForegroundColor Cyan
    Write-Host "  codex 'Show me the PDCA analysis phase prompt'"
} else {
    Write-Host "1. The skill is automatically discovered by Claude Code"
    Write-Host "2. Start a coding session: claude-code"
    Write-Host "3. Claude will use the skill when appropriate"
    Write-Host ""
    Write-Host "Test it:" -ForegroundColor Cyan
    Write-Host "  claude-code 'Show me the PDCA analysis phase prompt'"
}
Write-Host ""

# Documentation
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  README: $ScriptDir\README.md"
Write-Host "  Build:  $ScriptDir\BUILD.md"
Write-Host ""

# Uninstall instructions
Write-Host "To uninstall:" -ForegroundColor Cyan
Write-Host "  Remove-Item -Path `"$InstallDir`" -Recurse -Force"
Write-Host ""
