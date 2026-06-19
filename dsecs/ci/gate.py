#!/usr/bin/env python3
"""CI correctness gate.

Usage:
    python dsecs/ci/gate.py                  # runs a short canned trace
    python dsecs/ci/gate.py --experiments    # also runs experiment/test suite

Exits 0 on success, non-zero on failure.
"""

from __future__ import annotations
import sys
from ..core.state import State
from ..core.runtime import step
from ..gsa.objective import GSAI
from ..csco.constraint import CSCO
from ..ledger.store import InMemoryLedger
from ..ledger.replay import replay


def _is_monotonic(obj_values: list[float], eps: float = 1e-9) -> bool:
    for i in range(1, len(obj_values)):
        if obj_values[i] < obj_values[i - 1] - eps:
            return False
    return True


def ci_check(trace: list[State]) -> bool:
    """Run the three CI gates on a completed trace.

    1. All states satisfy CSCO.
    2. GSAI is non-decreasing (up to ε).
    3. Replay from ledger matches final hash.
    """
    # ---- Gate 1: CSCO invariant ----
    for s in trace:
        if not CSCO(s):
            print(f"❌ CI Gate 1 FAIL: CSCO violated at step {s.step}: "
                  f"failure_rate={s.failure_rate:.4f}, "
                  f"divergence={s.consensus_divergence:.4f}, "
                  f"memory_ok={s.memory_ok}")
            return False
    print("✅ CI Gate 1: All states satisfy CSCO constraints.")

    # ---- Gate 2: GSAI monotonic ----
    obj_vals = [GSAI(s) for s in trace]
    if not _is_monotonic(obj_vals):
        print("❌ CI Gate 2 FAIL: GSAI is not monotonic.")
        for i, (v, s) in enumerate(zip(obj_vals, trace)):
            marker = " ⬇" if i > 0 and v < obj_vals[i - 1] else ""
            print(f"   step {s.step}: GSAI={v:.6f}{marker}")
        return False
    print("✅ CI Gate 2: GSAI is non-decreasing.")

    # ---- Gate 3: Replay determinism ----
    ledger = InMemoryLedger()
    for s in trace:
        ledger.append(s)

    replayed_final = replay(ledger)
    original_final = trace[-1]
    if replayed_final.hash != original_final.hash:
        print(f"❌ CI Gate 3 FAIL: replay hash mismatch. "
              f"final={original_final.hash[:12]}… "
              f"replay={replayed_final.hash[:12]}…")
        return False
    print("✅ CI Gate 3: Replay is deterministic (hash match).")

    return True


def _canned_trace() -> list[State]:
    """Produce a short valid trace for gate testing."""
    ledger = InMemoryLedger()
    init = State(step=0, stability=1.0, failure_rate=0.0,
                 throughput=0.0, consensus_divergence=0.0, memory_ok=True)
    ledger.append(init)

    s = init
    for action in ("SYNC", "PROCESS", "RECOVER", "PROCESS"):
        s = step(s, action, ledger=ledger, seed=s.step)

    return ledger.states


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="DSECS CI Gate")
    parser.add_argument("--experiments", action="store_true",
                        help="Also run experiment & test suite")
    args = parser.parse_args()

    # Canned trace
    trace = _canned_trace()
    ok = ci_check(trace)

    if args.experiments:
        print("\n── Running experiments ──")
        from experiments.deterministic_test import run as det_run
        from experiments.byzantine_test import run as byz_run
        ok = ok and det_run()
        ok = ok and byz_run()

        print("\n── Running unit tests ──")
        import subprocess
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True, text=True)
        print(res.stdout)
        if res.returncode != 0:
            print(res.stderr)
            ok = False

    if ok:
        print("\n🎉 ALL GATES PASSED")
        return 0
    else:
        print("\n💥 SOME GATES FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
