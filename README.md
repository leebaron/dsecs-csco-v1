# DSECS Kernel

**Deterministic State Evolution Control System**

A constrained, replayable, CI-verifiable multi-agent control kernel.

`state → transition → CSCO → GSAI → ledger → replay → CI`

---

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run simulation
python main.py

# Run all tests
python -m pytest tests/ -v

# Run experiments
python experiments/simulate.py --steps 100 --nodes 3
python experiments/deterministic_test.py
python experiments/byzantine_test.py

# CI gate
python dsecs/ci/gate.py
```

### Docker

```bash
docker compose up --build
```

---

## Architecture

```
    GSAI (objective)
       ↑
state → transition → CSCO (hard gate) → next_state
       ↓
     ledger
       ↓
     replay    (determinism guarantee)
       ↓
     CI gate   (invariant check)
```

### Components

| Layer | File | Role |
|-------|------|------|
| **State** | `dsecs/core/state.py` | Immutable snapshot with hash-chained identity |
| **Transition** | `dsecs/core/transition.py` | Bounded stochastic dynamics (only dynamics) |
| **Runtime** | `dsecs/core/runtime.py` | Single kernel loop: CSCO → GSAI → ledger |
| **GSAI** | `dsecs/gsa/objective.py` | Global Stability & Autonomy Index (objective) |
| **CSCO** | `dsecs/csco/constraint.py` | Constraint-Satisfying Control Object (hard gate) |
| **Consensus** | `dsecs/consensus/majority.py` | Hash-based majority vote |
| **Ledger** | `dsecs/ledger/store.py` | Append-only hash-chained store |
| **Replay** | `dsecs/ledger/replay.py` | Deterministic reconstruction |
| **CI Gate** | `dsecs/ci/gate.py` | 3-invariant correctness check |
| **Simulation** | `experiments/simulate.py` | 3-node consensus simulation |
| **Determinism** | `experiments/deterministic_test.py` | Multi-run hash identity test |
| **Byzantine** | `experiments/byzantine_test.py` | Attack resilience test |

---

## Core Runtime

```python
def step(state, action, ledger=None, eps=1e-9, seed=None):
    candidate = transition(state, action, seed=seed)
    if not CSCO(candidate):         # hard constraint gate
        return state
    if GSAI(candidate) < GSAI(state) - eps:  # objective gate
        return state
    ledger.append(candidate)        # commit
    return candidate
```

---

## Theoretical Guarantee

**Constrained Convergence Theorem:**

- System trajectory remains bounded (CSCO feasible set is invariant)
- GSAI is non-decreasing up to ε
- Replay is deterministic and hash-verifiable
- Byzantine minority is rejected by majority consensus

---

## CI Pipeline

GitHub Actions executes:
1. `pytest` unit tests
2. `deterministic_test.py` — multi-run hash identity
3. `byzantine_test.py` — attack resilience
4. `simulate.py` — full simulation
5. `ci/gate.py` — 3-invariant final gate

---

## License

MIT
