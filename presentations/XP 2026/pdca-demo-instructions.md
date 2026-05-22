# PDCA Demo: Fixing an Unbounded Churn Ratio
  
A reproducible walkthrough of one full PDCA cycle — Plan → Do → Check → Act — using the
`code-quality-metrics` repo as the working example and Claude Code with the PDCA skill.
  
---
  
## What You Will Build
  
You will fix a real statistical defect: the `additions / max(deletions, 1)` churn ratio
produces unbounded values (e.g. p90 = 446x) for net-new-file commits, distorting the
p50/p90 distribution. The fix replaces it with a naturally bounded addition fraction
`additions / (additions + deletions)` ∈ [0, 1].
  
---
  
## Prerequisites
  
| Requirement | Version |
|---|---|
| Node.js | ≥ 18 |
| Git | any recent |
| Claude Code CLI | current |
| PDCA skill | installed (see below) |
| Beads CLI | optional (see below) |
  
---
  
## Step 1 — Install the PDCA Skill
  
Follow the **Quick Install** instructions for Claude Code in
[claude-skill/README.md — For Claude Code (Command Line)](https://github.com/kenjudy/pdca-framework/blob/main/claude-skill/README.md#for-claude-code-command-line).
  
The install script handles placing the skill in `~/.claude/skills/pdca-framework/` so it is available across all your projects.
  
**Verify:**
```bash
ls ~/.claude/skills/pdca-framework/
# Should show: SKILL.md and references/
```
  
### Optional: Install Beads for Persistent Task Tracking
  
To run this demo with the `plan with beads` and beads-tracked DO phase, follow the
**Beads Integration** section in the same README.
  
---
  
## Step 2 — Clone the Repo
  
```bash
git clone https://github.com/stride-nyc/code-quality-metrics.git
cd code-quality-metrics
npm install
```
  
If using beads, initialize it now:
  
```bash
bd init
```
  
Verify the test suite is clean before starting:
  
```bash
npm test
```
  
---
  
## Step 3 — Reset to the Demo Starting Point
  
The repo's working state already has the fix applied. This script stashes any local
changes and creates a fresh branch at the commit just before the fix, giving you the
broken code to work from:
  
```bash
bash temp-reset.sh
```
  
What the script does:
```bash
git stash
git switch -c $RANDOM 267fa1d19840b5a7215d6aac59dacb42df223bea
```
  
After running it, confirm you are on a new branch at the pre-fix state:
  
```bash
git log --oneline -3
# 267fa1d Merge pull request #16 from stride-nyc/enhanced-measurement
# ...
```
  
---
  
## Step 4 — Open Claude Code
  
```bash
claude
```
  
---
  
## Step 5 — Run the PDCA Cycle
  
Use these prompts in sequence. Each is a single message to Claude Code.
  
### PLAN — Analysis
  
```
Use the pdca skill to analyze the following change. Prepare and present the analysis to me
before proceeding to make an implementation plan using beads to track activity.
  
Fixing the unbounded `additions/deletions` churn ratio that distorts p50/p90. The
calculation additions / max(deletions, 1) for a commit of entirely new files yields a
ratio approaching infinity, which explodes both the median and p90. So, in a specific
analysis a p90=446x will skew "net-new-file commits". We need a statistically valid way
of analyzing churn. This is more important than backwards compatibility.
```
  
**Pause here.** Review the analysis Claude presents — the candidate approaches table and
the chosen metric — before approving the plan.
  
### PLAN — Create Implementation Plan with Beads
  
```
plan with beads
```
  
Claude will create a beads epic and seven subtasks (RED/GREEN pairs + CHECK). Review the
task board before proceeding.
  
### DO — Implement
  
```
Do
```
  
Claude will work through each step: write failing test → implement → confirm green →
close the beads task → move to next step. Each RED→GREEN cycle is one message exchange.
Intervene if TDD discipline breaks down.
  
#### Intervention Example: Trivial First Test
  
This happened in this session. The first RED test Claude wrote for step 1 was:
  
```js
test('change_ratio is 1.0 (not "inf") for a pure-addition commit with no deletions', () => {
execSync.mockReturnValue('446\t0\tsrc/new-feature.js');
const result = analyzeCommit(MOCK_SHA, MOCK_BRANCH);
expect(typeof result.change_ratio).toBe('number'); // fails: received "string"
expect(result.change_ratio).toBe(1.0); // fails: received "inf"
});
```
  
The test did fail on the broken code, so it was technically RED. But the first assertion
— `typeof result.change_ratio).toBe('number')` — is testing a JavaScript type, not a
business rule. It says nothing about why the value matters or what goes wrong when it is
wrong. A type check gives no signal about whether p50/p90 are being distorted.
  
The business failure is that a net-new-file commit registers as infinity and explodes the
distribution. A test grounded in the domain drops the `typeof` check and asserts the
bounded meaning directly:
  
```js
test('a net-new-file commit contributes 1.0 to the addition fraction, not infinity', () => {
execSync.mockReturnValue(numstatLine(446, 0, 'src/new-feature.js'));
const result = analyzeCommit(MOCK_SHA, MOCK_BRANCH);
expect(result.change_ratio).toBe(1.0); // 100% of changed lines are additions
expect(result.change_ratio).toBeLessThanOrEqual(1.0); // cannot inflate p50/p90
});
```
  
**Intervene when the first assertion tests language mechanics.** Use this prompt:
  
```
Stop. The typeof assertion tests JavaScript, not the domain.
  
The business rule is: a net-new-file commit must not inflate p50/p90. Write the
assertion that fails for that reason — not because the type is wrong.
```
  
### CHECK — Verify
  
```
check
```
  
Claude will run the completeness checklist against the plan and the Definition of Done.
  
### ACT — Retrospective
  
```
Act
```
  
Claude will facilitate the retrospective and store it on the closed beads epic.
  
### Optional: Deepen the Retrospective
  
```
If I were to change anything in my behavior, prompts or context, what one change could I
make to affect the improvement you suggest as the one thing to change?
```
  
---
  
## What a Complete Run Produces
  
| Artifact | Description |
|---|---|
| `lib/git.js` | `change_ratio` now `number \| null` in [0, 1] |
| `local-code-metrics.js` | Ratios array uses bounded formula, nulls filtered; summary fields renamed |
| `__tests__/analyzeCommit.test.js` | 4 new tests; old `'inf'` assertions replaced |
| `__tests__/statisticalDistribution.test.js` | 2 new boundedness contract tests |
| `__tests__/collectLocalMetrics.test.js` | Field rename assertions; bounded value assertions |
| Beads epic `code-quality-metrics-csi` | Full audit trail: analysis → subtasks → retrospective |
  
Expected final state: **120 tests passing**, lines 96%+, functions 96%+.
  
---
  
## Resetting Between Runs
  
To repeat the demo from scratch:
  
```bash
git checkout 267fa1d19840b5a7215d6aac59dacb42df223bea
git switch -c demo-$(date +%s)
```
  
Or re-run `temp-reset.sh` from the original branch.
  
---
  
## References
  
- PDCA skill install guide: [claude-skill/README.md](https://github.com/kenjudy/pdca-framework/blob/main/claude-skill/README.md)
- Beads integration: [claude-skill/README.md#beads-integration](https://github.com/kenjudy/pdca-framework/blob/main/claude-skill/README.md#beads-integration)
- Framework research and philosophy: [SOSA 2025 Notes](https://github.com/kenjudy/pdca-framework/blob/main/presentations/SOSA%202025/SOSA%202025%20Notes.md)