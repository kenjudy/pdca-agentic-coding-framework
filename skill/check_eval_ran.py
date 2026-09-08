"""Tell "the harness never ran" apart from "the scenario failed".

A shot that dies before reaching the API -- a missing build artifact, an absent key,
a network failure -- produces no scored result. But the runner's exit code is
non-zero either way, so a caller counting exit codes reports both as "did not pass",
which is indistinguishable from the model actually failing the scenario.

The first eval run of #131's Step 0 reported "5 shot(s); 5 did not pass" from a
harness that never called the API once. It read exactly like a confirmed hypothesis
and would have justified a prompt change on no evidence. eval/README.md states why
this class of defect is dangerous: a broken eval is self-sealing, because the eval
*is* the mechanism that was supposed to notice.

The evidence is already in the reports. EvalReporter renders a Summary table per
run; a shot that crashed before scoring anything leaves that table with a header, a
separator, and no data rows. So this is a pure function over report text -- it needs
no API key, no network and no live run, which is the point: it has to work in
exactly the conditions where the harness cannot.

    python3 check_eval_ran.py <results-dir> [<results-dir> ...]

Exits 0 when at least one scenario was scored, 1 when shots produced no verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

SUMMARY_HEADING = "## Summary"
# The rendered separator row; everything between it and the blank line is data.
SEPARATOR_PREFIX = "|---"


def scored_scenarios(report_text: str) -> list[str]:
    """Scenario ids that received a verdict in this report.

    An empty list means the run produced no measurement -- not that it measured a
    failure.
    """
    if SUMMARY_HEADING not in report_text:
        return []

    lines = report_text[report_text.index(SUMMARY_HEADING):].splitlines()
    scenarios, past_separator = [], False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(SEPARATOR_PREFIX):
            past_separator = True
            continue
        if not past_separator:
            continue
        if not stripped.startswith("|"):
            break  # table ended
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and cells[0]:
            scenarios.append(cells[0])
    return scenarios


def check_run(report_texts: list[str]) -> list[str]:
    """Return problems. Empty means the run produced at least one real verdict."""
    if not report_texts:
        return [
            "The eval run produced no report at all, so nothing was measured. "
            "This is a harness failure, not a scenario outcome -- do not read the "
            "runner's exit code as a verdict."
        ]

    if any(scored_scenarios(text) for text in report_texts):
        return []

    return [
        f"{len(report_texts)} report(s) were written but none contains a scored "
        "scenario, so the harness did not run to completion. Nothing was measured. "
        "Common causes: the skill was not built (references/ missing), the API key "
        "is absent, or the request never left the machine. Read the run log for the "
        "underlying error rather than treating this as a scenario outcome."
    ]


def _read_reports(paths: list[str]) -> list[str]:
    """Read reports from directories or individual files.

    Callers should pass only the reports THIS run produced. eval/results/ accumulates
    across runs, so a directory holding an earlier scored report would mask a current
    run that scored nothing -- the same stale-artifact hazard BUILD.md documents for
    the build.
    """
    texts: list[str] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            texts.extend(report.read_text() for report in sorted(path.glob("*.md")))
        elif path.is_file():
            texts.append(path.read_text())
    return texts


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"usage: {argv[0] if argv else 'check_eval_ran.py'} <results-dir> ...", file=sys.stderr)
        return 2

    texts = _read_reports(argv[1:])
    problems = check_run(texts)
    if problems:
        print("Eval harness check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    scored = sorted({s for text in texts for s in scored_scenarios(text)})
    print(f"Eval harness ran: {len(texts)} report(s), scored {', '.join(scored)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
