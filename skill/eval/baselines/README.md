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

```bash
cd skill && bash run-evals.sh tests/test_evals.py      # or dispatch evals.yml
cp eval/results/report_<timestamp>.md eval/baselines/
```

Promote a **full sweep**, not a single scenario — `test_baseline_exists_for_every_scenario`
requires every scenario in `eval/scenarios/` to appear in some baseline here.

## Reading a baseline

**Check the `**Environment:**` line first.** Every report records the `deepeval` and
`anthropic` versions that produced it (#145). Scores are not comparable across a major
dependency bump, and a report without that line predates the mechanism — treat its numbers
as unattributable, which is precisely why #122 could not be answered in retrospect.

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
