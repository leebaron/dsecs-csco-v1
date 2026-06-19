"""Deterministic replay from ledger history.

replay(log) must return exactly the final state that the original run produced.
This is the central determinism guarantee.
"""

from __future__ import annotations
from typing import Sequence
from ..core.state import State
from ..core.runtime import step
from .store import InMemoryLedger


def replay(ledger: InMemoryLedger) -> State:
    """Deterministically replay the full ledger and return the final state.

    Raises AssertionError if the replayed trace diverges from the stored one.
    """
    stored = ledger.states
    if not stored:
        raise ValueError("Cannot replay an empty ledger")

    # Use a fresh ledger for replay to isolate from original.
    replay_ledger = InMemoryLedger()

    # Bootstrap from the stored initial state (not re-derived).
    current = stored[0]

    for i, stored_s in enumerate(stored):
        if i == 0:
            # First state is the bootstrap — no action to replay.
            replay_ledger.append(current)
            continue

        action = stored_s.action
        assert action is not None, f"State {stored_s.step} has no action"

        # Seed: use the transition_seed stored in the state itself.
        # This is critical when steps are rejected (CSCO/GSAI gate)
        # — the seed counter keeps incrementing even though the state
        # doesn't advance, so deriving seed from step number is wrong.
        current = step(current, action, ledger=replay_ledger,
                       seed=stored_s.transition_seed)

        # Hash equality check at every step.
        assert current.hash == stored_s.hash, (
            f"Replay divergence at step {stored_s.step}: "
            f"replay={current.hash[:12]}… "
            f"!= stored={stored_s.hash[:12]}…"
        )

    return current
