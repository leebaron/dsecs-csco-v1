# DSECS — Security Model

## Threat Model

| Threat | Description | Severity |
|--------|-------------|----------|
| Adversarial input | Malicious state injected to bypass constraints | High |
| Inconsistent agent state | State divergence across nodes | High |
| Replay tampering | Attempt to modify logged decision history | Critical |
| State manipulation | Direct mutation of in-memory state | High |
| Byzantine behavior | Malicious node in multi-tenant environment | Medium |

## Mitigations

### CSCO Constraint Gate
- Every candidate state is validated against hard constraints
- `failure_rate < 0.20`, `consensus_divergence < 0.30`, `memory_ok == True`
- Violations cause immediate rejection — no execution path for unsafe state

### GSAI Bounded Evaluation
- Utility scoring is deterministic (same state → same score)
- Monotonicity check prevents GSAI degradation across transitions
- Score threshold (≥ 0.50) provides second layer of defense

### Ledger Hash-Chain Integrity
- Every state is SHA-256 hashed at creation
- Each append verifies `parent_hash == previous.hash`
- Tampering with any entry breaks the entire hash chain
- Detection is immediate — hash mismatch raises AssertionError

### Deterministic Replay
- Full state trajectory can be reconstructed from ledger
- Replay uses same transition function with stored seeds
- Any divergence between replay and original is caught by hash comparison
- CI gate verifies replay consistency as a hard invariant

## Guarantee

> **Tampering → Immediately detectable via hash mismatch.**
> No undetected state mutation is possible.

## Verification

```bash
# Run CI gate — verifies CSCO + GSAI + Replay invariants
python3 dsecs/ci/gate.py --experiments

# Manual replay check
python3 -c "
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay
# ... load ledger ...
replay(ledger)  # Raises AssertionError if tampered
"
```
