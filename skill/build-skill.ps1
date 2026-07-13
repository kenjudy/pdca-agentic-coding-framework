# Build script for PDCA Framework Claude Skill
# Composes skill package from master source files

$ErrorActionPreference = "Stop"  # Exit on error

Write-Host "Building PDCA Framework Skill..." -ForegroundColor Blue

# Paths
$ScriptDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent $ScriptDir
$BuildDir = Join-Path $ScriptDir "build"
$SrcDir = Join-Path $ScriptDir "src"

# Master source files
$Master1A = Join-Path (Join-Path $RepoRoot "1. Plan") "1a Analyze to determine approach for achieving the goal.md"
$Master1B = Join-Path (Join-Path $RepoRoot "1. Plan") "1b Create a detailed implementation plan.md"
$Master2 = Join-Path (Join-Path $RepoRoot "2. Do") "2. Test Drive the Change.md"
$MasterAntiPatterns = Join-Path (Join-Path $RepoRoot "2. Do") "Testing Anti-Patterns.md"
$Master3 = Join-Path (Join-Path $RepoRoot "3. Check") "3. Completeness Check.md"
$Master4 = Join-Path (Join-Path $RepoRoot "4. Act") "4. Retrospect for continuous improvement.md"
$MasterWorkingAgreements = Join-Path $RepoRoot "Human Working Agreements.md"

# Output files
$referencesPath = Join-Path $SrcDir "references"
$OutputPlan = Join-Path $referencesPath "plan-prompts.md"
$OutputDo = Join-Path $referencesPath "do-prompts.md"
$OutputCheck = Join-Path $referencesPath "check-prompts.md"
$OutputAct = Join-Path $referencesPath "act-prompts.md"
$OutputWorkingAgreements = Join-Path $referencesPath "working-agreements.md"
$OutputAntiPatterns = Join-Path $referencesPath "testing-anti-patterns.md"

# Verify master files exist
Write-Host "Verifying master source files..." -ForegroundColor Blue
$masterFiles = @($Master1A, $Master1B, $Master2, $MasterAntiPatterns, $Master3, $Master4, $MasterWorkingAgreements)
foreach ($file in $masterFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "Error: Master file not found: $file" -ForegroundColor Red
        exit 1
    }
}
Write-Host ([char]0x2713 + " All master files found") -ForegroundColor Green

# Create directories
$referencesDir = Join-Path $SrcDir "references"
if (-not (Test-Path $referencesDir)) {
    New-Item -ItemType Directory -Path $referencesDir -Force | Out-Null
}

# Build plan-prompts.md (combines 1a and 1b)
Write-Host "Building plan-prompts.md..." -ForegroundColor Blue
$planHeader = @"
# PLAN Phase: Analysis & Detailed Planning

This file contains prompts for both analysis (1a) and planning (1b) phases.

---

"@

$planContent = $planHeader
$planContent += Get-Content $Master1A -Raw
$planContent += [Environment]::NewLine + "---" + [Environment]::NewLine + [Environment]::NewLine
$planContent += Get-Content $Master1B -Raw
Set-Content -Path $OutputPlan -Value $planContent -NoNewline
Write-Host ([char]0x2713 + " Created plan-prompts.md") -ForegroundColor Green

# Build do-prompts.md
Write-Host "Building do-prompts.md..." -ForegroundColor Blue
Copy-Item $Master2 -Destination $OutputDo -Force
Write-Host ([char]0x2713 + " Created do-prompts.md") -ForegroundColor Green

# Build check-prompts.md
Write-Host "Building check-prompts.md..." -ForegroundColor Blue
Copy-Item $Master3 -Destination $OutputCheck -Force
Write-Host ([char]0x2713 + " Created check-prompts.md") -ForegroundColor Green

# Build act-prompts.md
Write-Host "Building act-prompts.md..." -ForegroundColor Blue
Copy-Item $Master4 -Destination $OutputAct -Force
Write-Host ([char]0x2713 + " Created act-prompts.md") -ForegroundColor Green

# Build working-agreements.md
Write-Host "Building working-agreements.md..." -ForegroundColor Blue
Copy-Item $MasterWorkingAgreements -Destination $OutputWorkingAgreements -Force
Write-Host ([char]0x2713 + " Created working-agreements.md") -ForegroundColor Green

# Build testing-anti-patterns.md
Write-Host "Building testing-anti-patterns.md..." -ForegroundColor Blue
Copy-Item $MasterAntiPatterns -Destination $OutputAntiPatterns -Force
Write-Host ([char]0x2713 + " Created testing-anti-patterns.md") -ForegroundColor Green

# SKILL.md is manually maintained, so we don't overwrite it
$skillMdPath = Join-Path (Join-Path $ScriptDir "pdca-framework") "SKILL.md"
if (-not (Test-Path $skillMdPath)) {
    Write-Host "Warning: SKILL.md not found. This file should be manually maintained." -ForegroundColor Red
}

# Create the .skill package (ZIP file with .skill extension)
Write-Host "Creating skill package..." -ForegroundColor Blue
$SkillFile = Join-Path $ScriptDir "pdca-framework.skill"

# Remove old skill file if it exists
if (Test-Path $SkillFile) {
    Remove-Item $SkillFile -Force
}

# Create temporary directory for packaging
$tempDir = Join-Path $ScriptDir "temp_package"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy files to temp directory
Copy-Item $skillMdPath -Destination $tempDir -Force
$tempReferencesDir = Join-Path $tempDir "references"
New-Item -ItemType Directory -Path $tempReferencesDir -Force | Out-Null
Copy-Item $OutputPlan -Destination $tempReferencesDir -Force
Copy-Item $OutputDo -Destination $tempReferencesDir -Force
Copy-Item $OutputCheck -Destination $tempReferencesDir -Force
Copy-Item $OutputAct -Destination $tempReferencesDir -Force
Copy-Item $OutputWorkingAgreements -Destination $tempReferencesDir -Force
Copy-Item $OutputAntiPatterns -Destination $tempReferencesDir -Force

# Create ZIP first (Compress-Archive only supports .zip extension)
$tempZipFile = Join-Path $ScriptDir "pdca-framework.zip"
Compress-Archive -Path "$tempDir\*" -DestinationPath $tempZipFile -Force

# Rename to .skill extension
if (Test-Path $tempZipFile) {
    Move-Item $tempZipFile $SkillFile -Force
}

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

# Verify the package was created
if (-not (Test-Path $SkillFile)) {
    Write-Host "Error: Failed to create skill package" -ForegroundColor Red
    exit 1
}

$SkillSize = (Get-Item $SkillFile).Length
$SkillSizeKB = [math]::Round($SkillSize / 1KB, 2)
Write-Host ([char]0x2713 + " Created pdca-framework.skill (${SkillSizeKB} KB)") -ForegroundColor Green

# Show what's in the package
Write-Host ""
Write-Host "Skill package contents:" -ForegroundColor Blue
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($SkillFile)
$zip.Entries | ForEach-Object {
    $size = $_.Length
    Write-Host "  $($_.FullName) (${size} bytes)"
}
$zip.Dispose()

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "Skill package: $SkillFile" -ForegroundColor Blue
Write-Host "Size: ${SkillSizeKB} KB" -ForegroundColor Blue
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Blue
Write-Host "1. Review the generated files in src/references/"
Write-Host "2. Install for Claude Code: Expand-Archive pdca-framework.skill -DestinationPath `$env:USERPROFILE\.claude\skills"
Write-Host "   Install for Codex:       Expand-Archive pdca-framework.skill -DestinationPath `$env:USERPROFILE\.agents\skills"
Write-Host "3. Upload pdca-framework.skill to Claude.ai, if needed"
Write-Host "4. Commit changes if everything looks good"
