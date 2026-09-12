"""EvalReporter: collects scenario results and writes a Markdown report."""

import hashlib
import importlib.metadata
import textwrap
from pathlib import Path

# Recorded in every report. A report that does not say what produced it cannot serve
# as a baseline: issue #122 asked whether deepeval 3.9.9 -> 4.x changed scenario
# scoring, and the question was unanswerable because every report on record carried a
# timestamp and nothing else. No run could be attributed to a version.
PROVENANCE_PACKAGES = ("deepeval", "anthropic")


def rubric_ladder_fingerprint(criteria_by_id: dict[str, str]) -> str:
    """Short, deterministic fingerprint of a set of rubric CRITERIA strings (#172).

    A rubric's bands and scaffold are a version, same as a dependency, but nothing
    recorded which version produced a given report. #153 added a scoring band to all
    five rubrics; #148 rewrote the shared bands and scaffold again. Either shifts scores
    by construction wherever a response lands in the newly affected range, so a GEval
    delta measured across such a change is not evidence of a prompt regression or
    improvement by itself -- see eval/baselines/README.md. A fingerprint lets a reader
    tell whether two reports share a rubric-ladder version without re-deriving it.

    A content hash rather than a git commit reference: a commit reference is fragile
    under shallow clones and squash merges, and it couples report generation to git
    state. This needs neither.

    Sorted by id and joined with an explicit separator between id and text -- an
    unseparated join lets {"1a": "X"} and {"1": "aX"} collide ("1a" + "X" ==
    "1" + "aX") despite different content.
    """
    combined = "\n".join(f"{rid}:{criteria_by_id[rid]}" for rid in sorted(criteria_by_id))
    return hashlib.sha256(combined.encode()).hexdigest()[:12]


def _installed_version(package: str) -> str:
    """Version of an installed distribution, without importing it.

    importlib.metadata reads distribution metadata off disk, so the reporter stays
    importable in the default unit suite, which installs neither of these. "not
    installed" is recorded rather than omitted -- a missing line reads as an older
    report format, while an explicit one records that the package genuinely was absent.
    """
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def compute_shot_stats(shot_scores: list[float]) -> dict:
    """Compute mean and sample stddev from a list of GEval shot scores.

    Uses sample stddev (divides by n-1) to avoid underestimating variance.
    Returns stddev of 0.0 when fewer than 2 scores are provided.
    """
    n = len(shot_scores)
    mean = sum(shot_scores) / n if n > 0 else 0.0
    if n < 2:
        stddev = 0.0
    else:
        variance = sum((s - mean) ** 2 for s in shot_scores) / (n - 1)
        stddev = variance ** 0.5
    return {"shot_mean": round(mean, 4), "shot_stddev": round(stddev, 4)}


def mechanical_passed(result: dict) -> bool:
    """Whether the mechanical tier passed for a result, retried or not.

    Was computed inline in two places with the same expression. Named because the
    divergence note below turns it into a comparison rather than a display value.
    """
    if result.get("retried"):
        return result["shots_mech_passed"] >= 2
    return all(c.passed for c in result["mechanical"])


PHASE_NAMES = {
    "1a": "Analysis",
    "1b": "Planning",
    "2": "TDD Implementation",
    "3": "Verification",
    "4": "Retrospection",
}


class EvalReporter:
    def __init__(self):
        self.results: list[dict] = []

    def add(self, result: dict) -> None:
        self.results.append(result)

    def write_report(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render())
        return path

    def _render(self) -> str:
        lines = []

        from datetime import datetime
        lines.append(f"# PDCA Eval Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Before the results, not after: this is the line that tells a reader whether
        # the scores below are comparable to the ones they are comparing them against.
        versions = ", ".join(f"{p}: {_installed_version(p)}" for p in PROVENANCE_PACKAGES)
        lines.append(f"**Environment:** {versions}\n")

        from eval.rubrics import RUBRICS

        ladder = rubric_ladder_fingerprint({rid: mod.CRITERIA for rid, mod in RUBRICS.items()})
        lines.append(f"**Rubric ladder:** {ladder}\n")

        # Summary table
        lines.append("## Summary\n")
        lines.append("| Scenario | Phase | Score | Threshold | GEval | Mechanical |")
        lines.append("|----------|-------|-------|-----------|-------|------------|")
        for r in self.results:
            phase = PHASE_NAMES.get(r["prompt_id"], r["prompt_id"])
            mech_ok = mechanical_passed(r)
            if r.get("retried"):
                mean = r.get("shot_mean")
                stddev = r.get("shot_stddev")
                if mean is not None and stddev is not None:
                    score_str = f"{mean} ± {stddev}"
                else:
                    score_str = f"{r['shots_geval_passed']}/{r['shots_total']} shots"
            else:
                score_str = f"{r['geval_score']:.2f}" if r["geval_score"] is not None else "n/a"
            lines.append(
                f"| {r['scenario_id']} | {phase} | {score_str} | {r['geval_threshold']:.2f}"
                f" | {'✅' if r['geval_passed'] else '❌'} | {'✅' if mech_ok else '❌'} |"
            )
        lines.append("")

        # Per-scenario detail
        lines.append("## Scenario Details\n")
        for r in self.results:
            phase = PHASE_NAMES.get(r["prompt_id"], r["prompt_id"])
            score_str = f"{r['geval_score']:.2f}" if r["geval_score"] is not None else "n/a"

            lines.append(f"### {r['scenario_id']} ({phase})\n")

            if r.get("retried"):
                lines.append(
                    f"**GEval:** retried — {r['shots_geval_passed']}/{r['shots_total']} shots passed"
                    f" {'✅' if r['geval_passed'] else '❌'}"
                )
                lines.append(f"\n**Mechanical:** {r['shots_mech_passed']}/{r['shots_total']} shots passed\n")
                for i, shot in enumerate(r["shots"], 1):
                    shot_score = f"{shot['geval_score']:.2f}" if shot["geval_score"] is not None else "n/a"
                    shot_mech_ok = all(c.passed for c in shot["mechanical"])
                    lines.append(
                        f"**Shot {i}:** GEval {shot_score} {'✅' if shot['geval_passed'] else '❌'}"
                        f" | Mechanical {'✅' if shot_mech_ok else '❌'}"
                    )
                    if shot.get("geval_reason"):
                        lines.append(f"> {shot['geval_reason'].strip()}")
                    # Every shot's output is kept. The shots that fail are the
                    # ones worth diagnosing, and a report that drops them makes
                    # post-hoc attribution impossible.
                    lines.append(f"\n<details><summary>Shot {i} output</summary>\n")
                    lines.append("```")
                    lines.append(shot["output"].strip())
                    lines.append("```")
                    lines.append("\n</details>")
                lines.append("")
            else:
                lines.append(
                    f"**GEval:** {score_str} / threshold {r['geval_threshold']:.2f}"
                    f" {'✅' if r['geval_passed'] else '❌'}"
                )

                # Mechanical checks
                lines.append("\n**Mechanical checks:**\n")
                if r["mechanical"]:
                    for c in r["mechanical"]:
                        lines.append(f"- {'✅' if c.passed else '❌'} `{c.field}` — {c.detail}")
                else:
                    lines.append("- *(none defined)*")

                # Judge reasoning
                if r.get("geval_reason"):
                    lines.append("\n**Judge reasoning:**\n")
                    lines.append(f"> {r['geval_reason'].strip()}")

            # Input
            lines.append("\n**Input:**\n")
            lines.append("```")
            lines.append(textwrap.dedent(r["input"]).strip())
            lines.append("```")

            # Model output
            lines.append("\n**Model output:**\n")
            lines.append("```")
            lines.append(r["output"].strip())
            lines.append("```")

            lines.append("")

        # Analyst notes: flag high-variance retried scenarios, and scenarios where the
        # two scoring tiers disagree.
        high_variance = [
            r for r in self.results
            if r.get("retried") and (r.get("shot_stddev") or 0.0) > 0.2
        ]
        # Mechanical confirms required strings are literally present; GEval judges
        # semantically. When they disagree the judge scored something the rubric may not
        # declare -- the fingerprint of a rubric fault rather than a scenario failure.
        # In #136, 17 of 18 retry-shots passed mechanically while 13 of 18 fell below the
        # GEval threshold, and both numbers sat on the same summary rows uncompared.
        divergent = [
            r for r in self.results
            if mechanical_passed(r) != r["geval_passed"]
        ]
        if high_variance or divergent:
            lines.append("## Analyst Notes\n")
        if high_variance:
            lines.append("The following scenarios show high score variance (stddev > 0.2) across retry shots.")
            lines.append("These may be flaky or sensitive to minor prompt wording changes.\n")
            for r in high_variance:
                lines.append(
                    f"- **{r['scenario_id']}**: mean={r.get('shot_mean')}, stddev={r.get('shot_stddev')}"
                )
            lines.append("")

        if divergent:
            lines.append("**Mechanical/GEval divergence**\n")
            lines.append(
                "The two scoring tiers disagree on these scenarios. The mechanical tier "
                "confirms the required strings are literally present; GEval judges "
                "semantically. A disagreement means the judge scored something the rubric "
                "may not declare, so this may be a rubric fault rather than a scenario "
                "failure -- read the recorded response before treating it as either "
                "(see #136).\n"
            )
            for r in divergent:
                mech = "pass" if mechanical_passed(r) else "FAIL"
                geval = "pass" if r["geval_passed"] else "FAIL"
                lines.append(f"- **{r['scenario_id']}**: mechanical {mech}, GEval {geval}")
            lines.append("")

        return "\n".join(lines)
