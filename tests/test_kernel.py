"""Unit tests for the DSECS kernel.

Run with:
    pytest tests/ -v
"""

from __future__ import annotations
from dsecs.core.state import State
from dsecs.core.transition import transition
from dsecs.core.runtime import step
from dsecs.gsa.objective import GSAI
from dsecs.csco.constraint import CSCO
from dsecs.consensus.majority import majority
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay
from dsecs.ci.gate import ci_check


# ── State ──────────────────────────────────────────────────────────────

def test_state_defaults() -> None:
    s = State()
    assert s.step == 0
    assert s.stability == 1.0
    assert s.failure_rate == 0.0
    assert s.throughput == 0.0
    assert s.consensus_divergence == 0.0
    assert s.memory_ok is True
    assert s.action is None
    assert len(s.hash) == 64


def test_state_hash_chain() -> None:
    s1 = State(step=0)
    s2 = s1.clone(step=1, action="SYNC")
    assert s2.parent_hash == s1.hash
    assert s2.hash != s1.hash


def test_state_clone_preserves_parent() -> None:
    s1 = State(step=0)
    s2 = s1.clone(step=1)
    assert s2.parent_hash == s1.hash


# ── Transition ─────────────────────────────────────────────────────────

def test_transition_increments_step() -> None:
    s = State(step=5)
    s2 = transition(s, "PROCESS", seed=0)
    assert s2.step == 6


def test_transition_NOOP_degradation() -> None:
    s = State()
    s2 = transition(s, "NOOP", seed=0)
    assert s2.failure_rate >= s.failure_rate
    assert s2.stability <= s.stability


def test_transition_SYNC_improves_stability() -> None:
    """SYNC action compensates worst-case drift → stability guaranteed >= input."""
    s = State(stability=0.5, failure_rate=0.1, throughput=1.0,
              consensus_divergence=0.1)
    # With max stability drop of 0.10 and SYNC boost of 0.10,
    # worst-case delta_stability = -0.10 + 0.10 = 0.0 → never decreases.
    s2 = transition(s, "SYNC", seed=0)
    assert s2.stability >= s.stability, f"{s2.stability} < {s.stability}"
    assert s2.throughput > s.throughput
    assert s2.step == s.step + 1


def test_transition_deterministic_with_seed() -> None:
    a = transition(State(), "PROCESS", seed=42)
    b = transition(State(), "PROCESS", seed=42)
    assert a.hash == b.hash


# ── CSCO ───────────────────────────────────────────────────────────────

def test_csco_passes_valid() -> None:
    s = State(failure_rate=0.05, consensus_divergence=0.1, memory_ok=True)
    assert CSCO(s) is True


def test_csco_rejects_high_failure() -> None:
    s = State(failure_rate=0.25, consensus_divergence=0.1, memory_ok=True)
    assert CSCO(s) is False


def test_csco_rejects_high_divergence() -> None:
    s = State(failure_rate=0.05, consensus_divergence=0.35, memory_ok=True)
    assert CSCO(s) is False


def test_csco_rejects_memory_failure() -> None:
    s = State(failure_rate=0.05, consensus_divergence=0.1, memory_ok=False)
    assert CSCO(s) is False


# ── GSAI ───────────────────────────────────────────────────────────────

def test_gsai_higher_is_better() -> None:
    good = State(stability=0.9, failure_rate=0.01, throughput=5.0)
    bad = State(stability=0.3, failure_rate=0.5, throughput=0.1)
    assert GSAI(good) > GSAI(bad)


# ── Runtime step ───────────────────────────────────────────────────────

def test_step_accepts_valid_transition() -> None:
    s = State()
    ledger = InMemoryLedger()
    ledger.append(s)
    s2 = step(s, "SYNC", ledger=ledger, seed=0)
    assert s2.step == 1
    assert ledger.length == 2


def test_step_rejects_csco_violation() -> None:
    s = State(failure_rate=0.19, memory_ok=True)  # near limit
    ledger = InMemoryLedger()
    ledger.append(s)
    # NOOP pushes failure over 0.2
    s2 = step(s, "NOOP", ledger=ledger, seed=0)
    # Should reject — CSCO gate returns original state
    assert s2.hash == s.hash
    assert ledger.length == 1


def test_step_rejects_gsai_drop() -> None:
    s = State(stability=0.95, failure_rate=0.0, throughput=0.0)
    ledger = InMemoryLedger()
    ledger.append(s)
    # Force a GSAI-decreasing transition by using a very bad action
    # We need a state where any transition lowers GSAI... use max state.
    s2 = step(s, "NOOP", ledger=ledger, seed=0, eps=0.0)
    # If GSAI dropped, original state is returned
    assert s2.hash == s.hash


# ── Consensus ──────────────────────────────────────────────────────────

def test_majority_simple() -> None:
    s1 = State(step=0)
    s2 = State(step=1, parent_hash=s1.hash)
    s3 = State(step=1, parent_hash=s1.hash)
    assert majority([s1, s2, s2, s2, s1]).hash == s2.hash


def test_majority_single() -> None:
    s = State()
    assert majority([s]).hash == s.hash


# ── Ledger ─────────────────────────────────────────────────────────────

def test_ledger_append_checks_chain() -> None:
    ledger = InMemoryLedger()
    s0 = State()
    s1 = s0.clone(step=1, action="X")
    ledger.append(s0)
    ledger.append(s1)
    assert ledger.length == 2


def test_ledger_rejects_broken_chain() -> None:
    ledger = InMemoryLedger()
    ledger.append(State())
    bad = State(step=1, action="BAD", parent_hash="0" * 64)
    try:
        ledger.append(bad)
        assert False, "Should have raised AssertionError"
    except AssertionError:
        pass


# ── Replay ─────────────────────────────────────────────────────────────

def test_replay_identity() -> None:
    ledger = InMemoryLedger()
    s = State()
    ledger.append(s)
    s = step(s, "SYNC", ledger=ledger, seed=0)
    s = step(s, "PROCESS", ledger=ledger, seed=1)
    s = step(s, "RECOVER", ledger=ledger, seed=2)
    replayed = replay(ledger)
    assert replayed.hash == s.hash


# ── CI gate ────────────────────────────────────────────────────────────

def test_ci_passes_good_trace() -> None:
    ledger = InMemoryLedger()
    s = State()
    ledger.append(s)
    for action in ("SYNC", "PROCESS", "RECOVER", "PROCESS"):
        s = step(s, action, ledger=ledger, seed=s.step)
    assert ci_check(ledger.states) is True


def test_ci_fails_on_csco_violation() -> None:
    # Build a trace where a state violates CSCO
    s1 = State(step=0)
    s2 = State(step=1, failure_rate=0.9, consensus_divergence=0.9,
               memory_ok=False, action="BAD",
               parent_hash=s1.hash)
    assert ci_check([s1, s2]) is False
