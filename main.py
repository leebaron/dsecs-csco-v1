#!/usr/bin/env python3
"""DSECS Kernel — entry point.

Run an interactive simulation, then verify with the CI gate.
"""

from __future__ import annotations
import sys

from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.gsa.objective import GSAI
from dsecs.csco.constraint import CSCO
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay
from dsecs.ci.gate import ci_check


def main() -> int:
    print("═══ DSECS Kernel v1.0 ═══")
    print("Deterministic State Evolution Control System\n")

    ledger = InMemoryLedger()
    # Start slightly degraded so first transitions can improve GSAI.
    s = State(step=0, stability=0.80, failure_rate=0.15,
              throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    ledger.append(s)

    actions = ["SYNC", "PROCESS", "RECOVER", "PROCESS", "SYNC",
               "NOOP", "PROCESS", "RECOVER", "SYNC", "PROCESS"]

    print(f"{'Step':<6} {'Action':<10} {'GSAI':<10} {'CSCO':<6} {'Stability':<10} "
          f"{'Failure':<10} {'Thrpt':<8} {'Div':<8} {'MemOK':<6}")
    print("-" * 80)

    for i, action in enumerate(actions):
        s2 = step(s, action, ledger=ledger, seed=s.step)
        accepted = s2.hash != s.hash
        step_no = s2.step  # always shows the candidate's step
        print(f"{step_no:<6} {action:<10} {GSAI(s2):<10.6f}"
              f"{' ✅' if accepted else ' ❌':<6} "
              f"{s2.stability:<10.4f} {s2.failure_rate:<10.4f} "
              f"{s2.throughput:<8.4f} {s2.consensus_divergence:<8.4f} "
              f"{'Y' if s2.memory_ok else 'N':<6}")
        if accepted:
            s = s2

    print(f"\nTotal ledger entries: {ledger.length}")
    print(f"Final GSAI: {GSAI(s):.6f}")
    print(f"Final CSCO: {'PASS' if CSCO(s) else 'FAIL'}")

    # CI gate
    print("\n── Running CI gate ──")
    ok = ci_check(ledger.states)

    # Deterministic replay verification
    print("\n── Running replay ──")
    try:
        replayed = replay(ledger)
        match = replayed.hash == s.hash
        print(f"{'✅' if match else '❌'} Replay {'MATCHES' if match else 'MISMATCHES'}")
        ok = ok and match
    except Exception as e:
        print(f"❌ Replay failed: {e}")
        ok = False

    print(f"\n{'🎉 ALL CHECKS PASSED' if ok else '💥 SOME CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
