# Eval baselines

Tracked, deliberately promoted eval reports. `CLAUDE.md`'s Validating Prompt Changes step 1
and `SUPERVISION-PROTOCOL.md`'s "Establish a Baseline" both point here.

## Why this is not `eval/results/`

`skill/eval/results/` is gitignored (`.gitignore:28`) and **has never been tracked** —
`git log --all` over that path returns nothing. Both instructions above used to point at
it, which meant they were inoperable on every fresh clone and in CI, and #122's closing
procedure ("compare against the baselines in `skill/eval/results/`") had no left-hand side.

`results/` cannot simply be un-ignored: every run writes a fresh timestamped report there,
so tracking it would leave the working tree dirty after each run — the churn pattern
`uv.lock` already produced. This directory holds only reports someone chose to promote.

## Promoting a report

A full sweep (`bash run-evals.sh` with no arguments) offers to promote itself (#159):

```
=== Harness check ===
Eval harness ran: 1 report(s), scored 21 scenarios.

## Verdict changed across runs
...

Promote report_<timestamp>.md to skill/eval/baselines/? [y/N]
```

Say yes and it's copied for you. **Only offered in a terminal, on a full sweep.** In
a non-interactive context — `evals.yml` on a GitHub Actions runner, no TTY on stdin —
it never prompts; it prints the `cp` command instead and moves on, since a blocking
prompt there would hang the job rather than fail loudly. A partial run (one scenario,
one class) is never offered either way, whatever the argument count claimed: it's
decided from the report's own content — does it score every scenario? — so a bug in
that argument-count check can't corrupt the baseline's completeness invariant.

To promote by hand instead:

```bash
cd skill && bash run-evals.sh tests/test_evals.py      # or dispatch evals.yml
cp eval/results/report_<timestamp>.md eval/baselines/
```

Either way, promote a **full sweep**, not a single scenario —
`test_baseline_exists_for_every_scenario` requires every scenario in `eval/scenarios/`
to appear in some baseline here.

## Reading a baseline

**Check the `**Environment:**` line first.** Every report records the `deepeval` and
`anthropic` versions that produced it (#145). Scores are not comparable across a major
dependency bump, and a report without that line predates the mechanism — treat its numbers
as unattributable, which is precisely why #122 could not be answered in retrospect.

**The rubric ladder itself is a version — check the `**Rubric ladder:**` line (#172).**
#153 added a `0.6 — Borderline` band to all five rubrics; #148 later rewrote the shared
bands and scaffold again. Either change shifts scores by construction wherever a response
lands in the newly affected range — the fix is meant to, that's the point — so a GEval
delta measured across such a change is not evidence of a prompt regression or improvement
by itself. Every report now records a short content fingerprint of all five rubrics'
assembled `CRITERIA` text; two reports with different fingerprints used different rubric
wording, whatever their timestamps say. A report from before this line existed (e.g.
`report_20260909_174245.md`, which predates both #153 and #172) carries no fingerprint at
all — treat a comparison against it the same way as a dependency-bump comparison above:
the fingerprint can only rule two reports *in* as comparable, never rule an unfingerprinted
one out.

**Mechanical checks are the reliable gate.** They were steady across every measured run
(17/18, 22/23, 17/18 on the #136 diagnostic).

**GEval scores for prompts 2 and 3 are provisional.** The Phase 2 rubric was measured
scoring identical behaviour anywhere from 0.00 to 0.90 (#136); two attempts to fix it by
editing the rubric made it worse and were reverted. #148 tracks the cause — rubrics score
every criterion against every scenario, including ones the scenario does not claim.
`2-superpowers-tdd-precedence` and `2-skip-tests-request` therefore carry `skip_geval`, and
#111 records the same class of problem in prompt 3.

Do not treat a prompt-2 or prompt-3 GEval delta as a regression without reading the
recorded responses, per `eval/README.md`'s materiality rule.

## Known reds in the current baseline

`report_20260909_174245.md` — 20 of 21 scenarios pass. **`4-tdd-breakdown` is red**
(GEval 0/3 shots, mechanical 3/3) and is tracked in #151: at least one shot shows the judge
scoring only the first line of a 1553-character response and reporting that the body was
absent. Treat it as a known red, not as a regression you introduced.

`4-short-session` carries high variance (mean 0.5667, stddev 0.3215) and passes on the mean.
