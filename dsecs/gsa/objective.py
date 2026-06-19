"""GSAI — Global Stability & Autonomy Index.

The scalar objective that the constrained system maximises.
Higher values → healthier system.
"""

from __future__ import annotations
from ..core.state import State


def GSAI(s: State) -> float:
    """Compute objective value for a given state.

    Weights:
        stability        × 1.0
        failure_rate     × -0.5
        throughput       × 0.3
    """
    return (
        s.stability
        - 0.5 * s.failure_rate
        + 0.3 * s.throughput
    )
