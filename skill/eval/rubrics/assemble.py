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

from collections.abc import Mapping

# Criteria render as "  1. text", with continuation lines carrying their own indentation
# verbatim inside the item. Nested numbered lists elsewhere in a rubric (rubric_2's Stub
# Discipline section has one) are part of the tail and are never renumbered -- renumbering
# them was the failure mode this format exists to avoid.
ITEM_PREFIX = "  {number}. "


def assemble(preamble: str, items: Mapping[str, str], tail: str) -> str:
    """Render preamble + the numbered criteria + tail.

    Numbering is positional over `items`, so it stays contiguous no matter which subset is
    passed. Item keys are stable identifiers for scenarios to reference; they never appear
    in the rendered text, so renaming one cannot change what the judge reads.
    """
    numbered = "\n".join(
        ITEM_PREFIX.format(number=n) + text for n, text in enumerate(items.values(), 1)
    )
    return preamble + numbered + "\n" + tail
