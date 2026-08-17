"""Significance test for interleaved A/B comparisons of prompt variants.

The eval harness is stochastic: scenarios fail on unmodified prompt text often
enough that a single run cannot attribute a failure to a prompt change. This
module answers the only question that matters when comparing two arms — is the
observed difference distinguishable from noise?

Fisher's exact test is used rather than a chi-square approximation because the
sample sizes involved (typically 6-12 runs per arm) are far too small for the
approximation to hold.
"""

import math


def fisher_exact_two_tailed(a: int, b: int, c: int, d: int) -> float:
    """Two-tailed Fisher exact test p-value for the 2x2 table [[a, b], [c, d]].

    Args:
        a: control arm passes
        b: control arm failures
        c: treatment arm passes
        d: treatment arm failures

    Returns:
        Probability of observing a table at least as extreme as this one, given
        no association between arm and outcome. Large values mean the arms are
        indistinguishable — i.e. no evidence the prompt change did anything.
    """
    row1, row2 = a + b, c + d
    col1 = a + c
    total = row1 + row2

    def table_probability(k: int) -> float:
        return (
            math.comb(row1, k)
            * math.comb(row2, col1 - k)
            / math.comb(total, col1)
        )

    observed = table_probability(a)
    # Sum every table at least as unlikely as the observed one. The epsilon
    # absorbs float error so symmetric tables are not dropped from the sum.
    return sum(
        p
        for k in range(max(0, col1 - row2), min(row1, col1) + 1)
        if (p := table_probability(k)) <= observed * (1 + 1e-9)
    )
