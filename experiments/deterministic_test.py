#!/usr/bin/env python3
"""Determinism stress test.

Runs the same simulation multiple times with identical seeds and verifies
that the resulting ledger traces are byte-identical.
"""

from __future__ import annotations
import sys

sys.path.insert(0, "..")

from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.ledger.store import InMemoryLedger


def _run(seed_offset: int) -> list[str]:
    """Simulate and return list of state hashes."""
    ledger = InMemoryLedger()
    # Start slightly degraded so first transitions can improve GSAI.
    s = State(step=0, stability=0.80, failure_rate=0.15,
              throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    ledger.append(s)
    actions = ["SYNC", "PROCESS", "RECOVER", "PROCESS", "SYNC",
               "PROCESS", "NOOP", "RECOVER", "PROCESS", "SYNC"]
    for i, a in enumerate(actions):
        s = step(s, a, ledger=ledger, seed=i + seed_offset)
    return [st.hash for st in ledger.states]


def run() -> bool:
    # All runs use IDENTICAL seed_offset=0 to test determinism.
    traces = [_run(seed_offset=0) for _ in range(5)]

    reference = traces[0]
    ok = True
    for i, trace in enumerate(traces[1:], start=1):
        if trace != reference:
            print(f"❌ Determinism violation: run {i} diverges from run 0")
            for j, (ref_h, test_h) in enumerate(zip(reference, trace)):
                if ref_h != test_h:
                    print(f"   step {j}: ref={ref_h[:16]}…  run{i}={test_h[:16]}…")
            ok = False

    if ok:
        print(f"✅ Determinism test: {len(traces)} identical runs, "
              f"{len(reference)} states each.")
    else:
        print("❌ Determinism test FAILED — hash chain differs across runs.")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
