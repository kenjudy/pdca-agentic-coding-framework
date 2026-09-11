"""Offer to promote a freshly-scored full eval sweep into skill/eval/baselines/ (#159).

Promotion into eval/baselines/ has been entirely manual since #152 created the
directory: `cp eval/results/report_<timestamp>.md eval/baselines/`, documented only in
baselines/README.md, prompted by nothing. Every full sweep since -- including the one
that validated #153's band-gap fix -- was read once and left in eval/results/,
gitignored, gone. #157's cross-run pooling needs an accumulating corpus and has had
nothing to pool over as a direct result.

run-evals.sh calls this after a successful run. Three properties, each guarding
against a specific way this could go wrong:

  NEVER BLOCKS NON-INTERACTIVELY. evals.yml dispatches run-evals.sh on a GitHub
  Actions runner with no TTY on stdin. A blocking prompt there would hang the job
  rather than fail loudly -- the opposite of every other fix in the eval harness this
  cycle (#141, #142, #156). isatty() is checked before anything that could read
  stdin; a non-interactive context prints the manual `cp` command and returns.

  A PARTIAL REPORT IS NEVER PROMOTABLE, REGARDLESS OF INTERACTIVITY OR ANSWER.
  test_baseline_exists_for_every_scenario requires every scenario in eval/scenarios/
  to appear in some baseline; promoting a partial sweep would corrupt that invariant
  silently. This is derived from the REPORT'S OWN CONTENT (does it score every
  scenario id?) rather than trusted from run-evals.sh's argument count, so a bug in
  the shell-side "was this a full sweep" gate cannot bypass it.

  THE DIVERGENCE SUMMARY IS SHOWN BEFORE ASKING, NOT AFTER. Silently overwriting a
  baseline that a scenario just regressed against would be worse than never
  prompting at all. Uses eval.aggregate, built for exactly this in #157.

    python3 promote_baseline.py <report.md>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

DEFAULT_BASELINES_DIR = Path(__file__).parent / "eval" / "baselines"
DEFAULT_SCENARIOS_DIR = Path(__file__).parent / "eval" / "scenarios"


def _all_scenario_ids(scenarios_dir: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted(scenarios_dir.glob("*.json")):
        scenarios = json.loads(path.read_text())
        if not isinstance(scenarios, list):
            scenarios = [scenarios]
        ids.update(s["scenario_id"] for s in scenarios)
    return ids


def _scored_scenario_ids(report_text: str) -> set[str]:
    """Scenario ids with a verdict in the report's Summary table.

    A smaller, local re-implementation of check_eval_ran.scored_scenarios rather than
    an import: that module's contract is "did the harness run at all", not "which
    scenarios", and coupling this script to its internals would make a change to
    either for the wrong reason break the other.
    """
    if "## Summary" not in report_text:
        return set()
    ids = set()
    lines = report_text[report_text.index("## Summary"):].splitlines()
    past_separator = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|---"):
            past_separator = True
            continue
        if not past_separator:
            continue
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and cells[0]:
            ids.add(cells[0])
    return ids


def _print_manual_instructions(report_path: Path, baselines_dir: Path, stream) -> None:
    print(
        f"Not promoting automatically. To do it yourself:\n\n"
        f"  cp {report_path} {baselines_dir}/\n",
        file=stream,
    )


def offer_promotion(
    report_path: Path,
    baselines_dir: Path = DEFAULT_BASELINES_DIR,
    scenarios_dir: Path = DEFAULT_SCENARIOS_DIR,
    *,
    stdin=None,
    stdout=None,
) -> bool:
    """Offer to promote report_path into baselines_dir. Returns whether it was promoted."""
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout

    report_text = report_path.read_text()
    missing = _all_scenario_ids(scenarios_dir) - _scored_scenario_ids(report_text)
    if missing:
        print(
            f"{report_path.name} scores {len(_scored_scenario_ids(report_text))} of "
            f"{len(_all_scenario_ids(scenarios_dir))} scenarios -- not a full sweep, "
            f"so it cannot become the baseline. Not prompting.",
            file=sys.stderr,
        )
        return False

    if not stdin.isatty():
        _print_manual_instructions(report_path, baselines_dir, sys.stderr)
        return False

    existing = sorted(baselines_dir.glob("report_*.md")) if baselines_dir.is_dir() else []
    if existing:
        from eval.aggregate import aggregate_reports, format_summary

        texts = [p.read_text() for p in existing] + [report_text]
        stdout.write(format_summary(aggregate_reports(texts)))
        stdout.write("\n")

    stdout.write(f"Promote {report_path.name} to skill/eval/baselines/? [y/N] ")
    stdout.flush()
    answer = stdin.readline().strip().lower()
    if answer != "y":
        _print_manual_instructions(report_path, baselines_dir, sys.stderr)
        return False

    baselines_dir.mkdir(parents=True, exist_ok=True)
    dest = baselines_dir / report_path.name
    shutil.copy(report_path, dest)
    print(f"Promoted to {dest}", file=stdout)
    return True


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"usage: python3 {Path(__file__).name} <report.md>", file=sys.stderr)
        return 2
    report_path = Path(argv[1])
    if not report_path.is_file():
        print(f"No such report: {report_path}", file=sys.stderr)
        return 2
    offer_promotion(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
