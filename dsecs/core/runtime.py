"""Core runtime loop — the single kernel entry point for state evolution.

Flow:
    state → transition → CSCO gate → GSAI monotonic check → ledger → next_state

This is the ONLY place where state advances.  No other code may mutate state.
"""

from __future__ import annotations
from .state import State
from .transition import transition
from ..gsa.objective import GSAI
from ..csco.constraint import CSCO
from ..ledger.store import InMemoryLedger


def step(state: State, action: str,
         ledger: InMemoryLedger | None = None,
         eps: float = 1e-9,
         seed: int | None = None) -> State:
    """One step of the deterministic constrained control loop.

    Args:
        state:  Current system state.
        action: String action identifier.
        ledger: Append-only ledger (optional; created if None).
        eps:    GSAI decrease tolerance.
        seed:   Deterministic RNG seed for transition.

    Returns:
        next_state if it passes CSCO ∧ GSAI monotonic, otherwise *state*.
    """
    candidate = transition(state, action, seed=seed)
    candidate.transition_seed = seed if seed is not None else -1

    # ---- CSCO hard constraint gate ----
    if not CSCO(candidate):
        return state

    # ---- GSAI monotonicity gate ----
    if GSAI(candidate) < GSAI(state) - eps:
        return state

    # ---- Ledger commit ----
    if ledger is not None:
        ledger.append(candidate)

    return candidate
