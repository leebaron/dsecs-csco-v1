#!/usr/bin/env python3
"""3-node DSECS simulation.

Launches N agents, each with an independent state.  At every tick:
  1. Each node proposes an action.
  2. Each node advances its own state via the kernel `step()`.
  3. Nodes exchange states and run majority consensus.
  4. The consensus state is committed to the ledger.

Usage:
    python experiments/simulate.py [--steps 100] [--nodes 3]
"""

from __future__ import annotations
import argparse
import random
import sys

sys.path.insert(0, "..")

from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.consensus.majority import majority
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay
from dsecs.ci.gate import ci_check

VALID_ACTIONS = ["PROCESS", "SYNC", "RECOVER", "NOOP"]


class Node:
    """A simulated DSECS node."""
    def __init__(self, node_id: int, seed: int):
        self.id = node_id
        self.rng = random.Random(seed)
        # Start slightly degraded so first transitions can improve GSAI.
        self.state = State(step=0, stability=0.80, failure_rate=0.15,
                           throughput=0.20, consensus_divergence=0.15,
                           memory_ok=True)

    def propose_action(self) -> str:
        """Choose an action — mostly good, occasionally NOOP."""
        return self.rng.choices(
            VALID_ACTIONS,
            weights=[0.60, 0.20, 0.10, 0.10],
        )[0]

    def tick(self, action: str, consensus_state: State) -> None:
        """Advance state using the consensus winner as current.
        Does NOT record in per-node ledger — the global ledger
        is the sole source of truth."""
        self.state = step(consensus_state, action,
                          seed=self.state.step)


def simulate(args: argparse.Namespace) -> tuple[list[State], bool]:
    n_nodes = args.nodes
    steps = args.steps

    nodes = [Node(i, seed=42 + i) for i in range(n_nodes)]
    global_ledger = InMemoryLedger()
    # Bootstrap from any node (all have identical initial hash).
    global_ledger.append(nodes[0].state)

    # All nodes start from the same bootstrap state.
    current = nodes[0].state

    for t in range(1, steps + 1):
        actions = [n.propose_action() for n in nodes]
        candidates = []
        for n, a in zip(nodes, actions):
            # Each node computes its candidate from current consensus state.
            cand = step(current, a, seed=current.step + t)
            candidates.append(cand)

        cons = majority(candidates)
        if cons.hash != current.hash:
            global_ledger.append(cons)
            current = cons

        # All nodes adopt the consensus state for the next tick.
        for n in nodes:
            n.state = current

    return global_ledger.states, True


def run(args: argparse.Namespace | None = None) -> bool:
    if args is None:
        args = argparse.Namespace(steps=100, nodes=3)
    trace, _ = simulate(args)

    ok = True
    print(f"Simulation ran {len(trace)-1} steps across {args.nodes} nodes.")
    print(f"Final state hash: {trace[-1].hash[:16]}…")
    print(f"Final GSAI: {trace[-1].stability - 0.5*trace[-1].failure_rate + 0.3*trace[-1].throughput:.6f}")

    # CI gate
    try:
        ok = ci_check(trace)
    except AssertionError as e:
        print(f"❌ CI gate raised: {e}")
        ok = False

    # Replay determinism (separate ledger path)
    ledger = InMemoryLedger()
    for s in trace:
        ledger.append(s)
    replayed = replay(ledger)
    replay_ok = replayed.hash == trace[-1].hash
    print(f"{'✅' if replay_ok else '❌'} Replay determinism: "
          f"{'MATCH' if replay_ok else 'MISMATCH'}")

    ok = ok and replay_ok
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DSECS 3-node simulation")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--nodes", type=int, default=3)
    a = parser.parse_args()
    ok = run(a)
    sys.exit(0 if ok else 1)
