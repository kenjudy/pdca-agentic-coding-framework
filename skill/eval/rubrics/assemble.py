"""Assemble a rubric's prompt text from addressable criteria (#148).

Rubrics were single monolithic strings, so `_rubric_for_prompt(prompt_id)` handed every
scenario in a phase the same criteria — including ones the scenario does not claim to
measure. That produced measured mis-scoring in rubrics 2 (#136), 3 (#111) and 4 (#151),
and `skip_geval`, the only lever for silencing it, is all-or-nothing.

Splitting the numbered criteria out makes them addressable so a scenario can later name
the ones that apply. When that lands, out-of-scope criteria will be **omitted** from the
assembled text, never mentioned: #149 measured the alternative twice, and a "do not
penalise X" clause reliably becomes "penalise X".

This module is deliberately dumb. It renumbers and joins; it makes no judgments about
content. `tests/test_rubrics.py` pins each assembled result byte-for-byte against the text
that shipped before decomposition, which is what makes phase 1 provably behaviour-neutral
and free to verify — no API spend can be required to confirm an identical prompt.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

# Criteria render as "  1. text", with continuation lines carrying their own indentation
# verbatim inside the item. Any nested numbered list inside a criterion's own item text
# (e.g. rubric_2's stub-discipline entry, formerly a standalone Stub Discipline section in
# the tail before #148 folded it into CRITERIA_ITEMS) is never renumbered by this function
# -- renumbering it was the failure mode this format exists to avoid.
ITEM_PREFIX = "  {number}. "


class UnknownCriterion(KeyError):
    """A scenario named a criterion its rubric does not define.

    Raised rather than ignored: a typo that silently resolved to "all criteria" or to
    "none" would produce a perfectly normal-looking report, and the scenario would be
    measuring something other than what it says.
    """


def assemble(
    preamble: str,
    items: Mapping[str, str],
    tail: str,
    selected: Iterable[str] | None = None,
) -> str:
    """Render preamble + the numbered criteria + tail.

    `selected` narrows to a subset by key; None means every criterion. Selection follows
    the rubric's own declared order, NOT the caller's -- otherwise the same subset would
    render differently depending on how a scenario happened to list its ids, and two
    scenarios' scores would stop being comparable.

    Numbering is positional over whatever survives selection, so it stays contiguous and
    the judge never sees a gap implying something was withheld. Item keys never appear in
    the rendered text, so renaming one cannot change what the judge reads.
    """
    chosen = items
    if selected is not None:
        wanted = set(selected)
        unknown = wanted - set(items)
        if unknown:
            raise UnknownCriterion(
                f"criteria not defined by this rubric: {sorted(unknown)}; "
                f"available: {sorted(items)}"
            )
        chosen = {key: text for key, text in items.items() if key in wanted}
        if not chosen:
            raise ValueError(
                "an empty criteria selection would hand the judge a rubric with no "
                "criteria at all -- use skip_geval if GEval should not run"
            )

    numbered = "\n".join(
        ITEM_PREFIX.format(number=n) + text for n, text in enumerate(chosen.values(), 1)
    )
    return preamble + numbered + "\n" + tail
