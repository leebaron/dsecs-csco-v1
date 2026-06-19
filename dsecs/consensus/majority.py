"""Simple majority consensus over a set of candidate states.

For the production kernel we use a hash-based majority: the state whose
hash appears most frequently wins.  Ties break lexicographically.
"""

from __future__ import annotations
from collections import Counter
from typing import Sequence
from ..core.state import State


def majority(candidates: Sequence[State]) -> State:
    """Pick the majority-winning state from a list of candidates."""
    if not candidates:
        raise ValueError("majority() called with empty candidate list")

    counter: Counter[str] = Counter(s.hash for s in candidates)
    best_hash = counter.most_common(1)[0][0]

    # Tie-breaking: lexicographically smallest hash among tied leaders
    top_count = counter.most_common(1)[0][1]
    tied = [h for h, c in counter.items() if c == top_count]
    if len(tied) > 1:
        best_hash = min(tied)

    for s in candidates:
        if s.hash == best_hash:
            return s

    raise RuntimeError("majority invariant violated — hash not found")
