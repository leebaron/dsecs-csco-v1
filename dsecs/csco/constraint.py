"""CSCO — Constraint-Satisfying Control Object.

Hard constraint gate: if ANY check fails, the candidate state is rejected.
"""

from __future__ import annotations
from ..core.state import State


def CSCO(s: State) -> bool:
    """Return True iff *s* satisfies all hard system constraints."""
    return (
        s.failure_rate < 0.2
        and s.consensus_divergence < 0.3
        and s.memory_ok
    )
