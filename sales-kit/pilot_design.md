# DSECS — Pilot Design v1.0

**Goal:** Integrate DSECS into one real decision workflow and validate correctness, safety enforcement, and replayability.
**Stage:** First enterprise integration
**Status:** Ready

---

## 1. Ideal Pilot Customer

- AI agent platform (tool calling / workflows)
- Fintech decision engine
- Automation SaaS (pipeline execution)
- Compliance-sensitive AI feature team

---

## 2. Integration Model (Minimal Intrusion)

```
Their System
    ↓
DSECS API (middleware)
    ↓
CSCO → GSAI → Ledger
    ↓
Decision Result
```

### API Contract

**Decision Request:**
```
POST /v1/execute
{
  "action": "approve_loan",
  "context": {
    "amount": 50000,
    "risk": "medium"
  }
}
```

**Response:**
```json
{
  "status": "approved",
  "csco": "passed",
  "gsai_score": 0.78,
  "ledger_hash": "0xabc123..."
}
```

**Replay:**
```
GET /v1/replay/{ledger_hash}
→ returns identical decision trace
```

---

## 3. What the Pilot Proves

### Technical Proof
- Deterministic execution — no drift across runs
- Audit chain intact — every decision linked by hash
- Safety enforcement — CSCO blocks invalid states

### Business Proof
- Reduces decision risk — unsafe outputs never execute
- Enables compliance logging — full replay available
- Introduces governance layer — bounded scoring + audit

---

## 4. Success Criteria (Non-Negotiable)

```
Pilot success =
  ✔ 1 real workflow integrated
  ✔ 100+ decisions processed
  ✔ 0 inconsistency in replay
  ✔ 1 stakeholder says "we need this"
```

---

## 5. Onboarding Flow

### Step 1 — Connect API
- API key issued
- Endpoint configured (`POST /v1/execute`)

### Step 2 — Wrap One Decision
**Before:**
```
system executes decision directly
```

**After:**
```
system → DSECS → decision returned
```

### Step 3 — Observe Logs
- CSCO reject cases
- GSAI scoring distribution
- Ledger replay validation

### Step 4 — Validation Call
Ask one question:

> "Can you reproduce every decision your system made?"

---

## 6. SLA Model (Light Version)

- Deterministic guarantee
- Replay consistency
- Audit log retention (per agreement)
- Bounded evaluation consistency

---

## 7. Pilot Commercial Structure

| Phase | Duration | Model |
|-------|----------|-------|
| Phase 1 | 7–14 days | Free pilot |
| Phase 2 | Month-to-month | Usage-based pricing |
| Phase 3 | Annual | Enterprise contract (audit + SLA) |

---

## 8. Core Positioning (Final)

> DSECS is a decision middleware that enforces constraint, evaluation, and auditability for AI systems.

---

## 9. Integration Checklist

- [ ] API key provisioned
- [ ] Endpoint configured
- [ ] First decision wrapped
- [ ] CSCO/GSAI logs reviewed
- [ ] Ledger replay verified
- [ ] 100+ decisions processed
- [ ] Validation call completed

---

## 10. Final State

```
DSECS v1.0
├── Kernel:   frozen
├── Product:  live
├── GTM:      active
├── Launch:   ready
├── Execution: ongoing
├── Pilot:    ready
└── Stage:    first enterprise integration
```
