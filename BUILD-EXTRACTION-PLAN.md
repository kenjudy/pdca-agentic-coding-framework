# Implementation Plan: Extract a Shared Builder (#114)

> **Working artifact.** Delete before merging to `main`.
>
> **Branch:** `claude/fix-build-skill-ps1-drift-114` (off `main` @ `52feb86`)
> **Produced by:** PDCA PLAN phase (1a + 1b), Opus 5, 2026-08-17
> **Issue:** [#114](https://github.com/kenjudy/pdca-agentic-coding-framework/issues/114)
> **Status:** approved scope (Option B), not started

---

## Goal

After this cycle, `build-skill.sh` and `build-skill.ps1` are thin wrappers over a single
`skill/build.py`. Both platforms produce byte-identical packages because they run the same
code — drift becomes structurally impossible rather than merely detectable.

---

## Why extraction, not repair

`build-skill.ps1` has silently diverged through four separate feature additions. The root cause
is `build-skill.ps1:12` — `$SrcDir = Join-Path $ScriptDir "src"` — pointing at a directory the
repo renamed to `pdca-framework/` (branch `40-rename-src-to-pdca-framework`). Nothing has ever
executed it in CI, so nothing signalled.

Repairing it in place restores parity today and rebuilds the same trap: two implementations
that must stay in sync, with only a test standing between us and a fifth divergence. Extraction
removes the second implementation.

**Dependency check (verified, not assumed):** this adds nothing for shell users. `build-skill.sh`
already shells out to `python3` (line 103) for injection processing, and `uv`/Python is required
for the test suite. Bash users never touch pwsh; Windows users never touch bash. Packaging moves
from `zip -r` to Python's `zipfile`, which *removes* a dependency — Git Bash for Windows does not
ship `zip`.

---

## The five defects this closes

All demonstrated empirically against PowerShell 7.4.6 on 2026-08-17:

| # | Defect | Evidence |
|---|---|---|
| 1 | Wrong ZIP root | sh: `pdca-framework/SKILL.md` · ps1: `SKILL.md`. `build-skill.sh:223` marks this a marketplace requirement |
| 2 | 9 of 16 files missing | all 6 beads addons, the export script, both ponytail files |
| 3 | Raw `CLAUDE_INJECT` markers shipped | 6 markers across 4 prompt files; `plan-prompts.md` carries 3 |
| 4 | License blocks not stripped | 5 files |
| 5 | Creates untracked `skill/src/` | not gitignored — every Windows build pollutes the tree |

Since people build on Windows, a Windows-built package installs to the wrong path: `unzip -o
pdca-framework.skill -d ~/.claude/skills/` splats files loose instead of creating
`~/.claude/skills/pdca-framework/`.

---

## Behavior `build.py` must reproduce exactly

The existing 148-test suite is the acceptance criteria — it asserts file list, addon/source
fidelity, license stripping, injection replacement, and master-content matching against the
*packaged zip*. Extraction is correct when all of it stays green.

Mechanics that must be preserved to the byte:

| Behavior | Current implementation | Note |
|---|---|---|
| License strip | `sed '/^## License & Attribution/,$ d'` | Deletes from the matching line to EOF. Anchored at line start. A file without the heading passes through unchanged. |
| `plan-prompts.md` | header + `strip(1a)` + `"\n---\n"` + `strip(1b)` | It is a **concatenation**, not a copy |
| Injection | replace `<!-- CLAUDE_INJECT: {key} -->` with injection file content `.rstrip("\n")` | key = injection filename stem |
| Anti-patterns | plain `cp`, **not** license-stripped | asymmetry with the other five — preserve it |
| Addon files | plain `cp`, **not** license-stripped | `beads-setup.md` carries a license block deliberately |
| ZIP root | `pdca-framework/` | marketplace requirement |
| Exec bit | `export-requirements.sh` is `-rwxr-xr-x` in the zip | **`zipfile` drops permissions unless `external_attr` is set explicitly. No current test catches this.** |

---

## Steps

Each step is one commit. **Stop for review after each.** RED and GREEN stay separate commits so
each RED can be checked out and verified in isolation.

| # | Type | Model | Step | Called shot / acceptance |
|---|---|---|---|---|
| 0 | prep | — | Record the current bash build as reference: `unzip -Z` listing (names + permission bits) and SHA256 per member | Baseline captured before any change |
| 1 | `test:` **RED** | Sonnet 5 | Add `tests/test_builder.py::test_builder_produces_expected_manifest` — imports `build`, calls its entry point into a temp dir, asserts the zip namelist equals `EXPECTED_FILES` | Expected failure, one test: `ModuleNotFoundError: No module named 'build'` |
| 2 | `feat:` GREEN | **Opus 5** | Create `skill/build.py` implementing the full build per the table above | Step-1 test passes **and all 148 existing tests stay green**. Large by necessity — see note below |
| 3 | `test:` **RED** | Sonnet 5 | Add `test_export_script_is_executable` — asserts the packaged `export-requirements.sh` has the owner-execute bit in `external_attr` | Expected failure: mode `0o644`, expected `0o755`. **Verify this fails before fixing** — if it passes, `zipfile` preserved the bit and the test is vacuous |
| 4 | `feat:` GREEN | Sonnet 5 | Set `external_attr` on the script member in `build.py` | Step-3 test passes |
| 5 | `refactor:` | Sonnet 5 | Reduce `build-skill.sh` to a thin wrapper invoking `python3 build.py` | All tests green before and after. `run-tests.sh` drives `build-skill.sh`, so the suite exercises the wrapper |
| 6 | `test:` **RED** | Sonnet 5 | Add `test_powershell_build_matches_bash` — runs `build-skill.ps1`, compares namelist and per-member SHA256 against the bash build. `skipTest` when `pwsh` is absent | Expected failure: namelist mismatch — ps1 produces 7 root-level entries vs 16 under `pdca-framework/`. **Must be observed failing**, not skipped |
| 7 | `feat:` GREEN | Sonnet 5 | Rewrite `build-skill.ps1` as a thin wrapper invoking `python build.py`; delete the stale `$SrcDir` logic | Step-6 test passes. `skill/src/` no longer created |
| 8 | `ci:` | Sonnet 5 | Ensure CI runs the pwsh test — confirm `pwsh` is present on `ubuntu-latest` and the test does not silently skip in CI | A skipped parity test in CI is the same undetected-drift condition this cycle exists to end |
| 9 | `docs:` | Sonnet 5 | `skill/BUILD.md` (7 references incl. "Edit `build-skill.ps1` and update these variables"), `AGENTS.md:78`, `CHANGELOG.md` | Docs describe the wrapper architecture, not the old dual-implementation |

**On Step 2's size.** ~200 lines in one GREEN is larger than this project's norm. Decomposing it
would need scaffolding tests for intermediate states that get deleted at the end, because the
existing suite cannot run until a zip exists. The 148 existing assertions constrain the
implementation tightly enough that it is guided, not freehand — but review this commit carefully
rather than trusting the green.

---

## Risks

| Risk | Mitigation |
|---|---|
| Silent behavior change in license stripping or injection | The 148-test suite asserts packaged content against sources; Step 0's SHA256 baseline catches anything it misses |
| `zipfile` drops the exec bit | Steps 3–4 exist specifically for this. **It must be seen red first** — a passing Step 3 means the test is vacuous |
| `pwsh` absent in CI → Step 6 skips forever | Step 8. A skipped parity test is indistinguishable from no test |
| Wrapper swallows a non-zero exit | Both wrappers must propagate `build.py`'s exit code — `run-tests.sh` uses `set -e` and relies on it |
| Extraction changes ZIP member order or timestamps | Compare by sorted namelist and per-member hash, not archive bytes |

**Rollback:** every step is its own commit; Steps 5 and 7 are the only ones that change existing
entry points, and either reverts independently.

---

## Definition of Done

- [ ] `cd skill && bash run-tests.sh` green (currently 148 passed, 153 subtests)
- [ ] `mypy eval tests` clean; `build.py` type-clean under the project's mypy config
- [ ] `pwsh` parity test **observed failing at Step 6 and passing at Step 7** — not skipped
- [ ] Packaged `export-requirements.sh` retains `-rwxr-xr-x`
- [ ] Bash-built and PowerShell-built packages have identical namelists and per-member hashes
- [ ] No `skill/src/` created by any build path
- [ ] Docs updated (BUILD.md, AGENTS.md, CHANGELOG)
- [ ] Human sign-off on CHECK and ACT

## CHECK step

Verify against this plan's acceptance criteria. Confirm the two builds are byte-identical by
hash, not by inspection. Confirm the pwsh test ran rather than skipped, locally and in CI.

## ACT step

Retrospective. Specifically: whether extraction actually removed the drift class or relocated
it, and whether Step 2's single large GREEN was the right call or should have been decomposed.

## Notes for the executing session

- **`pwsh` is not installed by default in the dev container.** Install with:
  `curl -fsSL -o /tmp/pwsh.tar.gz https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/powershell-7.4.6-linux-x64.tar.gz && mkdir -p /opt/pwsh && tar -xzf /tmp/pwsh.tar.gz -C /opt/pwsh && chmod +x /opt/pwsh/pwsh`
  Verified working 2026-08-17. Without it, Step 6 skips and proves nothing.
- **`uv sync --extra test` rewrites `uv.lock` wholesale** in this container (revision bump plus
  dependency upgrades). Run `git checkout -- skill/uv.lock` before committing.
- **`skill/pdca-framework/references/` is gitignored and never cleaned by the build.** Stale
  artifacts survive a branch switch and make two builds look identical. `rm -rf` it before any
  comparison.
