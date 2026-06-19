"""In-memory append-only ledger with hash chain integrity.

Each append stores (state_hash, action, parent_hash) so that replay
can deterministically reconstruct the trajectory.
"""

from __future__ import annotations
from typing import List, Optional
from ..core.state import State


class InMemoryLedger:
    """Append-only, hash-chained, in-memory ledger."""

    def __init__(self) -> None:
        self._states: list[State] = []

    @property
    def length(self) -> int:
        return len(self._states)

    @property
    def states(self) -> List[State]:
        return list(self._states)

    def append(self, state: State) -> None:
        """Append a state, verifying hash-chain integrity."""
        if self._states:
            prev = self._states[-1]
            assert state.parent_hash == prev.hash, (
                f"Hash chain broken at step {state.step}: "
                f"parent_hash={state.parent_hash[:12]}… "
                f"!= prev.hash={prev.hash[:12]}…"
            )
        self._states.append(state)

    def last(self) -> Optional[State]:
        return self._states[-1] if self._states else None

    def reset(self) -> None:
        self._states.clear()
