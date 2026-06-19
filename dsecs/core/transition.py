"""State transition function — the only dynamics in the system."""

from __future__ import annotations
import random
from .state import State

# Rough upper bound on per-step drift to keep dynamics bounded.
MAX_STABILITY_DROP = 0.10
MAX_FAILURE_RISE  = 0.05
THROUGHPUT_NOISE  = 0.20
DIVERGENCE_NOISE  = 0.05


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def transition(state: State, action: str, seed: int | None = None) -> State:
    """Deterministic (w.r.t. seed) state transition.

    A *valid* action nudges the system forward; invalid/noop returns a
    near-identical state (possibly with degraded failure_rate / divergence
    to let CSCO reject it).
    """
    rng = random.Random(seed) if seed is not None else random.Random()

    # ------------------------------------------------------------------
    # Every action puts some pressure on the system.
    # ------------------------------------------------------------------
    delta_stability = -rng.uniform(0.0, MAX_STABILITY_DROP)
    delta_failure   = rng.uniform(0.0, MAX_FAILURE_RISE)
    delta_thrpt     = rng.gauss(0.0, THROUGHPUT_NOISE)
    delta_div       = rng.uniform(0.0, DIVERGENCE_NOISE)

    # "NOOP" actions intentionally degrade to test CSCO rejection.
    if action == "NOOP":
        delta_stability -= 0.03
        delta_failure   += 0.02
        delta_div       += 0.02

    # High-quality actions lift throughput and reduce divergence.
    if action in ("SYNC", "RECOVER"):
        delta_stability += 0.10  # compensates worst-case -0.10 drift
        delta_failure   -= 0.01
        delta_thrpt     += 0.5
        delta_div       -= 0.02

    next_state = state.clone(
        step=state.step + 1,
        stability=_clamp(state.stability + delta_stability),
        failure_rate=_clamp(state.failure_rate + delta_failure),
        throughput=max(0.0, state.throughput + delta_thrpt),
        consensus_divergence=_clamp(state.consensus_divergence + delta_div),
        action=action,
    )

    # Memory OK is determined by resource pressure (failure_rate proxy).
    next_state.memory_ok = next_state.failure_rate < 0.3

    return next_state
