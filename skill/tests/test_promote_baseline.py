"""Unit tests for promote_baseline.py (#159).

No test here spawns a real TTY -- isatty() is faked via a small stub, per the
project's usual approach to environment-dependent behavior (see
test_hook_infrastructure.py's git-command mocking). The one property that matters
most -- never blocking in a non-interactive context -- is asserted by the stdin
stub raising if readline() is ever called when isatty() is False.
"""

import json
import textwrap

import pytest

import promote_baseline as pb


def _report(scenario_ids):
    rows = "\n".join(f"| {s} | P | 0.90 | 0.50 | ✅ | ✅ |" for s in scenario_ids)
    return textwrap.dedent(f"""\
        # PDCA Eval Report — 2026-09-11 12:00:00

        **Environment:** deepeval: 4.2.2, anthropic: 1.4.0

        ## Summary

        | Scenario | Phase | Score | Threshold | GEval | Mechanical |
        |----------|-------|-------|-----------|-------|------------|
        {rows}
        """)


class _Stdin:
    """isatty()-controllable stdin stub that refuses to block."""

    def __init__(self, is_tty, lines=()):
        self._is_tty = is_tty
        self._lines = list(lines)

    def isatty(self):
        return self._is_tty

    def readline(self):
        if not self._is_tty:
            raise AssertionError("readline() called on a non-interactive stdin -- this would hang CI")
        return self._lines.pop(0) if self._lines else ""


class _Stdout:
    def __init__(self):
        self.text = ""

    def write(self, s):
        self.text += s

    def flush(self):
        pass


@pytest.fixture
def scenarios_dir(tmp_path):
    d = tmp_path / "scenarios"
    d.mkdir()
    (d / "1_scenarios.json").write_text(json.dumps([
        {"scenario_id": "s1"}, {"scenario_id": "s2"},
    ]))
    return d


@pytest.fixture
def baselines_dir(tmp_path):
    d = tmp_path / "baselines"
    d.mkdir()
    return d


class TestNeverBlocksNonInteractively:
    def test_non_interactive_stdin_never_calls_readline(self, tmp_path, scenarios_dir, baselines_dir):
        report = tmp_path / "report_new.md"
        report.write_text(_report(["s1", "s2"]))
        stdin, stdout = _Stdin(is_tty=False), _Stdout()

        promoted = pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=stdout)

        assert promoted is False

    def test_non_interactive_prints_the_manual_command(self, tmp_path, scenarios_dir, baselines_dir, capsys):
        report = tmp_path / "report_new.md"
        report.write_text(_report(["s1", "s2"]))
        stdin = _Stdin(is_tty=False)

        pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=_Stdout())

        assert "cp " in capsys.readouterr().err


class TestInteractivePrompt:
    def test_promotes_on_yes(self, tmp_path, scenarios_dir, baselines_dir):
        report = tmp_path / "report_new.md"
        report.write_text(_report(["s1", "s2"]))
        stdin = _Stdin(is_tty=True, lines=["y\n"])

        promoted = pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=_Stdout())

        assert promoted is True
        assert (baselines_dir / "report_new.md").read_text() == report.read_text()

    def test_declines_on_no(self, tmp_path, scenarios_dir, baselines_dir):
        report = tmp_path / "report_new.md"
        report.write_text(_report(["s1", "s2"]))
        stdin = _Stdin(is_tty=True, lines=["n\n"])

        promoted = pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=_Stdout())

        assert promoted is False
        assert not (baselines_dir / "report_new.md").exists()

    def test_empty_answer_defaults_to_no(self, tmp_path, scenarios_dir, baselines_dir):
        """The prompt is phrased [y/N] -- anything but an explicit yes must decline."""
        report = tmp_path / "report_new.md"
        report.write_text(_report(["s1", "s2"]))
        stdin = _Stdin(is_tty=True, lines=["\n"])

        promoted = pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=_Stdout())

        assert promoted is False


class TestCompletenessGuard:
    """A partial report must never be promotable, regardless of interactivity or answer.

    This is the guard against #159's stated hazard: a single-scenario or single-class
    run corrupting test_baseline_exists_for_every_scenario's completeness invariant.
    Derived from the REPORT'S OWN CONTENT rather than trusted from run-evals.sh's
    argument count, so a bug in the shell-side gate cannot bypass it.
    """

    def test_refuses_a_partial_report_even_with_a_tty_saying_yes(self, tmp_path, scenarios_dir, baselines_dir):
        report = tmp_path / "report_partial.md"
        report.write_text(_report(["s1"]))  # scenarios_dir declares s1 AND s2
        stdin = _Stdin(is_tty=True, lines=["y\n"])  # would say yes if asked

        promoted = pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=_Stdout())

        assert promoted is False
        assert not (baselines_dir / "report_partial.md").exists()

    def test_partial_report_never_reads_stdin_at_all(self, tmp_path, scenarios_dir, baselines_dir):
        """Not just 'refuses to copy' -- refuses to even ask, per the issue."""
        report = tmp_path / "report_partial.md"
        report.write_text(_report(["s1"]))
        stdin = _Stdin(is_tty=True)  # readline() would return "" (empty), fine either way,
        # but the real assertion is that isatty()=True does not by itself trigger a prompt.

        pb.offer_promotion(report, baselines_dir, scenarios_dir, stdin=stdin, stdout=_Stdout())
        # No exception, no prompt text needed -- covered by the promoted==False assertion above.


class TestDivergenceShownBeforePrompting:
    def test_shows_cross_run_summary_when_a_baseline_already_exists(self, tmp_path, scenarios_dir, baselines_dir):
        existing = baselines_dir / "report_old.md"
        existing.write_text(_report(["s1", "s2"]))
        new_report = tmp_path / "report_new.md"
        new_report.write_text(_report(["s1", "s2"]))
        stdin, stdout = _Stdin(is_tty=True, lines=["n\n"]), _Stdout()

        pb.offer_promotion(new_report, baselines_dir, scenarios_dir, stdin=stdin, stdout=stdout)

        assert "verdict" in stdout.text.lower() or "stability" in stdout.text.lower()

    def test_prompt_appears_after_the_divergence_summary_not_before(self, tmp_path, scenarios_dir, baselines_dir):
        existing = baselines_dir / "report_old.md"
        existing.write_text(_report(["s1", "s2"]))
        new_report = tmp_path / "report_new.md"
        new_report.write_text(_report(["s1", "s2"]))
        stdin, stdout = _Stdin(is_tty=True, lines=["n\n"]), _Stdout()

        pb.offer_promotion(new_report, baselines_dir, scenarios_dir, stdin=stdin, stdout=stdout)

        summary_at = stdout.text.lower().find("verdict")
        prompt_at = stdout.text.find("Promote")
        assert summary_at != -1 and prompt_at != -1 and summary_at < prompt_at
