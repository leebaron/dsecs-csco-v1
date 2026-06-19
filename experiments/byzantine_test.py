#!/usr/bin/env python3
"""Byzantine fault injection test.

Injects a malicious node that sends garbage states.  Verifies that:
  - The system stays within CSCO bounds.
  - GSAI is non-decreasing.
  - The honest majority overrides the byzantine node.

Usage:
    python experiments/byzantine_test.py [--byzantine-ratio 0.33]
"""

from __future__ import annotations
import argparse
import random
import sys

sys.path.insert(0, "..")

from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.core.transition import transition
from dsecs.consensus.majority import majority
from dsecs.ledger.store import InMemoryLedger
from dsecs.ci.gate import ci_check

VALID_ACTIONS = ["PROCESS", "SYNC", "RECOVER", "NOOP"]


def _malicious_state(base: State) -> State:
    """Produce a deliberately bad state (high failure, broken memory)."""
    return State(
        step=base.step,
        stability=random.uniform(0.0, 0.3),
        failure_rate=random.uniform(0.3, 0.9),
        throughput=0.0,
        consensus_divergence=random.uniform(0.5, 1.0),
        memory_ok=False,
        action="MALICIOUS",
        parent_hash=base.parent_hash,
    )


def simulate_byzantine(steps: int, n_nodes: int, byzantine_count: int,
                       seed: int = 42) -> list[State]:
    """Run simulation with *byzantine_count* malicious nodes."""
    rng = random.Random(seed)
    is_byzantine = [i < byzantine_count for i in range(n_nodes)]

    # Each honest node gets its own RNG so they propose different actions.
    # This ensures at least one honest candidate passes the GSAI gate
    # (e.g., SYNC/RECOVER), preventing all-from-original-state consensus.
    node_rngs = [random.Random(seed + i) for i in range(n_nodes)]

    init = State(step=0, stability=0.60, failure_rate=0.18,
                 throughput=0.10, consensus_divergence=0.15, memory_ok=True)
    states = [init] * n_nodes

    global_ledger = InMemoryLedger()
    global_ledger.append(init)

    for t in range(1, steps + 1):
        candidates = []
        for i in range(n_nodes):
            if is_byzantine[i]:
                # Byzantine: send a state that must NOT pass CSCO
                candidates.append(_malicious_state(states[i]))
            else:
                action = node_rngs[i].choice(VALID_ACTIONS)
                cand = step(states[i], action, seed=states[i].step + t)
                candidates.append(cand)

        cons = majority(candidates)
        # Only advance the ledger on actual state change.
        # This avoids hash-chain breakage when all honest nodes'
        # proposals are rejected (GSAI gate) and consensus falls
        # back to the original state.
        if cons.hash != global_ledger.last().hash:
            global_ledger.append(cons)

        # Honest nodes adopt consensus; byzantine nodes are ignored by design.
        for i in range(n_nodes):
            if not is_byzantine[i]:
                states[i] = cons

    return global_ledger.states


def run(args: argparse.Namespace | None = None) -> bool:
    n_nodes = 5
    byzantine_ratio = 0.33 if args is None else args.byzantine_ratio
    byzantine_count = max(1, int(n_nodes * byzantine_ratio))

    print(f"Byzantine test: {n_nodes} nodes, {byzantine_count} malicious "
          f"({byzantine_ratio:.0%})")
    print(f"  Honest majority: {n_nodes - byzantine_count} > {byzantine_count} "
          f"→ CSCO gate should reject all malicious proposals.")

    trace = simulate_byzantine(steps=100, n_nodes=n_nodes,
                               byzantine_count=byzantine_count)

    print(f"  Ledger length: {len(trace)} states")

    # Check no malicious state leaked into ledger
    leaked = [s for s in trace if s.action == "MALICIOUS"]
    if leaked:
        print(f"❌ Byzantine test FAIL: {len(leaked)} malicious states in ledger.")
        return False
    print("✅ No malicious states leaked into global ledger.")

    # CI gate
    try:
        ok = ci_check(trace)
    except AssertionError as e:
        print(f"❌ CI gate raised: {e}")
        ok = False

    if ok:
        print("✅ Byzantine test PASSED — system remains safe under attack.")
    else:
        print("❌ Byzantine test FAILED.")

    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DSECS Byzantine test")
    parser.add_argument("--byzantine-ratio", type=float, default=0.33)
    a = parser.parse_args()
    sys.exit(0 if run(a) else 1)
