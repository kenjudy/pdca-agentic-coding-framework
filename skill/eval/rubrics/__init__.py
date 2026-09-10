"""Rubric registry and per-scenario criteria selection (#148)."""

from __future__ import annotations

from collections.abc import Mapping

from eval.rubrics import rubric_1a, rubric_1b, rubric_2, rubric_3, rubric_4
from eval.rubrics.assemble import assemble

RUBRICS = {
    "1a": rubric_1a,
    "1b": rubric_1b,
    "2": rubric_2,
    "3": rubric_3,
    "4": rubric_4,
}


def rubric_for_scenario(prompt_id: str, expected_signals: Mapping[str, object]) -> tuple[str, float]:
    """The criteria text and threshold to judge one scenario against.

    Without `geval_criteria` a scenario gets its phase's whole rubric, which is the
    behaviour every scenario had before #148 -- so this is a no-op until a scenario opts
    in. With it, the named criteria are the only ones rendered; the rest are omitted
    entirely rather than mentioned as exclusions (#149).

    Lives here rather than in tests/test_evals.py because that file is excluded from the
    default suite, so selection logic there would be untested everywhere.
    """
    module = RUBRICS.get(prompt_id)
    if module is None:
        raise ValueError(f"No rubric registered for prompt_id: {prompt_id!r}")

    selected = expected_signals.get("geval_criteria")
    if not selected:
        return module.CRITERIA, module.THRESHOLD

    # eval/schema.py validates this, but the harness is the last place a malformed
    # selection can still be caught before it reaches the judge -- and a wrong type here
    # would silently render a rubric nobody intended.
    if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
        raise TypeError(
            f"geval_criteria must be a list of strings, got {selected!r}"
        )

    criteria = assemble(module.PREAMBLE, module.CRITERIA_ITEMS, module.TAIL, selected=selected)
    return criteria, module.THRESHOLD
