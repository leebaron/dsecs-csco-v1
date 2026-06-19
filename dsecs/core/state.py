"""System state representation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import json


@dataclass
class State:
    """Immutable system state snapshot.

    Fields:
        step:        Monotonic step counter.
        stability:   [0, 1] — system stability metric.
        failure_rate:[0, 1] — observed failure proportion.
        throughput:  [0, +∞) — actions processed per interval.
        consensus_divergence:[0, 1] — max deviation from consensus.
        memory_ok:   True iff memory/resource constraints satisfied.
        action:           The action that led to this state.
        transition_seed:  RNG seed used in transition (-1 for initial).
        parent_hash:      SHA-256 hex digest of predecessor state.
        hash:             SHA-256 hex digest of this state.
    """
    step: int = 0
    stability: float = 1.0
    failure_rate: float = 0.0
    throughput: float = 0.0
    consensus_divergence: float = 0.0
    memory_ok: bool = True
    action: Optional[str] = None
    transition_seed: int = -1
    parent_hash: str = "0" * 64
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        raw = json.dumps({
            "step": self.step,
            "stability": self.stability,
            "failure_rate": self.failure_rate,
            "throughput": self.throughput,
            "consensus_divergence": self.consensus_divergence,
            "memory_ok": self.memory_ok,
            "action": self.action,
            "transition_seed": self.transition_seed,
            "parent_hash": self.parent_hash,
        }, sort_keys=True)
        self.hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "stability": self.stability,
            "failure_rate": self.failure_rate,
            "throughput": self.throughput,
            "consensus_divergence": self.consensus_divergence,
            "memory_ok": self.memory_ok,
            "action": self.action,
            "transition_seed": self.transition_seed,
            "parent_hash": self.parent_hash,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> State:
        return cls(
            step=d["step"],
            stability=d["stability"],
            failure_rate=d["failure_rate"],
            throughput=d["throughput"],
            consensus_divergence=d["consensus_divergence"],
            memory_ok=d["memory_ok"],
            action=d.get("action"),
            transition_seed=d.get("transition_seed", -1),
            parent_hash=d.get("parent_hash", "0" * 64),
        )

    def clone(self, **overrides) -> State:
        """Produce a new State with selective field overrides."""
        kw = {
            "step": self.step,
            "stability": self.stability,
            "failure_rate": self.failure_rate,
            "throughput": self.throughput,
            "consensus_divergence": self.consensus_divergence,
            "memory_ok": self.memory_ok,
            "action": self.action,
            "transition_seed": self.transition_seed,
            "parent_hash": self.hash,
        }
        kw.update(overrides)
        return State(**kw)
