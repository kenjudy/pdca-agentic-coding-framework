"""EvalReporter: collects scenario results and writes a Markdown report."""

import textwrap
from pathlib import Path


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

        # Summary table
        lines.append("## Summary\n")
        lines.append("| Scenario | Phase | Score | Threshold | GEval | Mechanical |")
        lines.append("|----------|-------|-------|-----------|-------|------------|")
        for r in self.results:
            phase = PHASE_NAMES.get(r["prompt_id"], r["prompt_id"])
            mech_ok = r["shots_mech_passed"] >= 2 if r.get("retried") else all(c.passed for c in r["mechanical"])
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

        # Analyst notes: flag high-variance retried scenarios
        high_variance = [
            r for r in self.results
            if r.get("retried") and (r.get("shot_stddev") or 0.0) > 0.2
        ]
        if high_variance:
            lines.append("## Analyst Notes\n")
            lines.append("The following scenarios show high score variance (stddev > 0.2) across retry shots.")
            lines.append("These may be flaky or sensitive to minor prompt wording changes.\n")
            for r in high_variance:
                lines.append(
                    f"- **{r['scenario_id']}**: mean={r.get('shot_mean')}, stddev={r.get('shot_stddev')}"
                )
            lines.append("")

        return "\n".join(lines)
