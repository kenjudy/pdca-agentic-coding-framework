---
name: update-changelog
description: Updates a project changelog with entries for changes since the branch diverged from main. Use when about to open a PR, cutting a release, or when the user asks about changelog, release notes, or migration notes.
---

# Update Changelog

## Step 0 — Bind the version

If an argument that looks like a version number was provided (e.g.,
`v1.2.0`, `1.2.0`, `v2.0.0-rc.1`), store it as `VERSION`, normalising
to include a `v` prefix if absent. Otherwise VERSION defaults to
`Unreleased`.

**STOP gate:** Verify `CHANGELOG.md` exists in the repo root using the
Read tool. If it does not exist, report "CHANGELOG.md not found at repo
root." and halt.

## Step 1 — Get today's date

Run `date +%Y-%m-%d` and store the result as `TODAY`.

## Step 2 — Draft entries from commits

Run:

```sh
git log --oneline main..HEAD
```

Store the result as `COMMIT_LIST`. If the command fails, report the error and halt.

**STOP gate:** If `COMMIT_LIST` is empty, tell the user: "No commits found ahead of `main` — nothing to changelog. Is that expected?" and halt.

Draft changelog entries from `COMMIT_LIST`. Group them under `### Category` subheadings. Use the categories that best match the changes (e.g., `### New Skills`, `### PDCA Framework Redesigns`, `### Beads and Workflow`, `### Build and Distribution`, `### Dependency Updates`, `### Documentation`). Prefer the established category names from the existing changelog over inventing new ones.

Classify each entry as one of:

- **Regular entry** — new feature, bug fix, config change, anything user-visible
- **Migration note** — anything requiring user action: renamed files or commands, removed options, changed install paths, new required config keys

Skip internal-only changes (refactors, test additions, CI tweaks) that are not user-visible — do not propose entries for them.

## Step 3 — Review with user

**STOP gate:** If no entries were drafted, halt without writing — do not create an empty heading.

Print the proposed changelog block in chat. If VERSION is `Unreleased`,
the heading will be `## Unreleased`; if a version was provided, it will
be `## VERSION (TODAY)` (e.g., `## v1.2.0 (2026-06-01)` — substitute
the actual bound values). Below the block, print `COMMIT_LIST` under a
`**Commits for reference:**` label.

Ask: "Does this look right? (yes / no / paste edits)"
Wait for the response before continuing.

- If yes: proceed to Step 4.
- If no: halt without writing.
- If the user provides edited text: replace the draft with their version,
  then proceed to Step 4.

## Step 4 — Write the entries

On confirmation, write the entries to `CHANGELOG.md`.

**If VERSION is `Unreleased`:**
- If no `## Unreleased` heading exists, insert one at the top of the changelog body (below any `# Title` line), followed by a `---` separator before the first pre-existing versioned section.
- If `## Unreleased` already exists, append the new category subheadings and entries to it; do not create a duplicate heading.

**If VERSION is a version number (e.g., `v1.2.0`):**
- If no `## Unreleased` heading exists, insert a new `## VERSION (TODAY)`
  heading at the top of the changelog body (e.g., `## v1.2.0 (2026-06-01)`).
- If `## Unreleased` exists, rename it to `## VERSION (TODAY)` rather
  than creating a duplicate.

**New `## Unreleased` section** (none exists yet):

```markdown
## Unreleased

### New Skills
- My new skill

### Migration Notes  ← omit this subsection if there are no migration notes
- Thing the user must do manually

---

## v1.1.0 (2026-05-28)  ← existing versioned section follows the --- separator
```

**Appending to an existing `## Unreleased` section:**

```markdown
## Unreleased

### New Skills
- Earlier entry
- My new skill  ← append here

### PDCA Framework Redesigns
- My change  ← add new category subheading if not present; append if already present

### Migration Notes  ← add subsection if not present; append if already present
- Thing the user must do manually
```

**Versioned heading** (cutting a release):

```markdown
## v1.2.0 (2026-05-27)

### New Skills
- My feature

### Migration Notes  ← omit if none
- Thing the user must do manually
```
