"""Pool eval verdicts across runs (#147 deliverable 2).

`EvalReporter`'s Analyst Notes flag high variance within one run, and #147's divergence
note flags the two scoring tiers disagreeing. Neither can answer the question that
actually decides whether a scenario is usable as a regression gate: **does its verdict
change from run to run?**

That question needs several reports, and the reporter cannot see them. Its fixture is
`scope="session"`, so each `run-evals.sh` invocation writes its own file holding at most
3 retry-shots for a scenario. The bimodal distribution that diagnosed #136 was visible
only across ten separate reports, and nothing in the project reads them back --
`evals.yml`'s multi-shot dispatch produces exactly that data and then drops it.

WHAT THIS DELIBERATELY DOES NOT DO: attribute a cause. #147 as filed proposed flagging
bimodal scores as "judge instability". That was corrected -- the scoring bands are
1.0/0.7/0.4/0.0 against a 0.50 threshold in every rubric (#153), so a gap at the
threshold is partly structural and a shape alone cannot separate an unstable judge from
an unstable model. Naming a cause here would be #141's defect one level up: output that
reads like a measurement. This reports what happened and points at the scenarios worth
reading.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SUMMARY_HEADING = "## Summary"
SEPARATOR_PREFIX = "|---"
DETAILS_HEADING = "## Scenario Details"

# "**Shot 2:** GEval 0.90 ✅ | Mechanical ✅"
SHOT_RE = re.compile(r"\*\*Shot \d+:\*\*\s*GEval\s+([\d.]+)")
# "### 4-short-session (Retrospection)"
DETAIL_HEAD_RE = re.compile(r"^###\s+(\S+)")


@dataclass
class ScenarioRun:
    """One scenario's result in one report."""

    geval_passed: bool
    mechanical_passed: bool
    scores: list[float] = field(default_factory=list)


@dataclass
class ScenarioAggregate:
    """One scenario pooled across reports."""

    runs: int = 0
    passes: int = 0
    fails: int = 0
    divergent_runs: int = 0
    scores: list[float] = field(default_factory=list)

    @property
    def verdict_unstable(self) -> bool:
        """Both outcomes were observed. A fact, not a diagnosis -- but a scenario that
        does this cannot serve as a gate, whatever the cause."""
        return self.passes > 0 and self.fails > 0


def _shots_by_scenario(text: str) -> dict[str, list[float]]:
    """Per-shot GEval scores from the Scenario Details section, keyed by scenario."""
    if DETAILS_HEADING not in text:
        return {}
    shots: dict[str, list[float]] = {}
    current: str | None = None
    for line in text[text.index(DETAILS_HEADING):].splitlines():
        head = DETAIL_HEAD_RE.match(line.strip())
        if head:
            current = head.group(1)
            continue
        if current is None:
            continue
        found = SHOT_RE.search(line)
        if found:
            shots.setdefault(current, []).append(float(found.group(1)))
    return shots


def parse_report(text: str) -> dict[str, ScenarioRun]:
    """Scenario results from one rendered report.

    Verdicts come from the Summary table, which states them unambiguously. Scores come
    from the individual shots where a scenario was retried -- a retried row renders
    "mean ± stddev", which is not a score anyone observed. A skipped GEval renders "n/a"
    and contributes no score at all; treating that as 0.0 would invent a measurement.
    """
    if SUMMARY_HEADING not in text:
        return {}

    shots = _shots_by_scenario(text)
    results: dict[str, ScenarioRun] = {}
    past_separator = False

    for line in text[text.index(SUMMARY_HEADING):].splitlines():
        stripped = line.strip()
        if stripped.startswith(SEPARATOR_PREFIX):
            past_separator = True
            continue
        if not past_separator:
            continue
        if not stripped.startswith("|"):
            break

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 6 or not cells[0]:
            continue
        scenario, _, score_cell, _, geval, mechanical = cells[:6]

        scores = shots.get(scenario, [])
        if not scores:
            single = re.fullmatch(r"[\d.]+", score_cell)
            if single:
                scores = [float(score_cell)]

        results[scenario] = ScenarioRun(
            geval_passed="✅" in geval,
            mechanical_passed="✅" in mechanical,
            scores=scores,
        )
    return results


def aggregate_reports(report_texts: list[str]) -> dict[str, ScenarioAggregate]:
    """Pool scenario results across reports.

    Requires more than one report. A single run cannot show instability, and reporting
    "stable" from one observation is the claim CLAUDE.md explicitly warns against: "A
    single eval run cannot tell you whether your prompt edit caused a failure."
    """
    if len(report_texts) < 2:
        raise ValueError(
            "aggregation needs at least two reports -- a single run cannot show whether a "
            "verdict is stable, and calling it stable from one observation is exactly the "
            "inference CLAUDE.md warns against"
        )

    pooled: dict[str, ScenarioAggregate] = {}
    for text in report_texts:
        for scenario, run in parse_report(text).items():
            agg = pooled.setdefault(scenario, ScenarioAggregate())
            agg.runs += 1
            if run.geval_passed:
                agg.passes += 1
            else:
                agg.fails += 1
            if run.geval_passed != run.mechanical_passed:
                agg.divergent_runs += 1
            agg.scores.extend(run.scores)
    return pooled


def format_summary(pooled: dict[str, ScenarioAggregate]) -> str:
    """Render the pooled result.

    States what was observed and where to look. Says nothing about why -- see the module
    docstring.
    """
    lines = ["# Cross-run verdict stability", ""]
    lines.append(f"Scenarios pooled: {len(pooled)}")
    lines.append("")

    unstable = {s: a for s, a in sorted(pooled.items()) if a.verdict_unstable}
    if not unstable:
        lines.append("No scenario changed verdict across the reports supplied.")
    else:
        lines.append("## Verdict changed across runs")
        lines.append("")
        lines.append(
            "These scenarios both passed and failed. Whatever the cause, a scenario that "
            "does this cannot serve as a regression gate -- read the recorded responses "
            "in the reports before treating any single run of it as a result."
        )
        lines.append("")
        for scenario, agg in unstable.items():
            spread = ""
            if agg.scores:
                spread = f", scores {min(agg.scores):.2f}–{max(agg.scores):.2f}"
            diverged = (
                f", tiers disagreed in {agg.divergent_runs} of {agg.runs}"
                if agg.divergent_runs
                else ""
            )
            lines.append(
                f"- **{scenario}**: {agg.passes} pass / {agg.fails} fail "
                f"over {agg.runs} run(s){spread}{diverged}"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv:
        print(f"usage: python {Path(__file__).name} <report.md|dir> [...]", file=sys.stderr)
        return 2

    texts: list[str] = []
    for arg in argv:
        path = Path(arg)
        files = sorted(path.glob("*.md")) if path.is_dir() else [path]
        texts.extend(f.read_text() for f in files if f.is_file())

    if len(texts) < 2:
        print(
            f"Found {len(texts)} report(s). Aggregation needs at least two -- a single run "
            "cannot show whether a verdict is stable.",
            file=sys.stderr,
        )
        return 2

    print(format_summary(aggregate_reports(texts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
