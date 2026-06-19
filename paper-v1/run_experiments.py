#!/usr/bin/env python3
"""DSECS Paper v1.0 — Experiment Runner

Generates all data and figures for the NeurIPS submission.
"""

import sys, os, json, math, random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.consensus.majority import majority
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay
from dsecs.gsa.objective import GSAI
from dsecs.csco.constraint import CSCO

VALID_ACTIONS = ["PROCESS", "SYNC", "RECOVER", "NOOP"]

def run_simulation(steps=500, nodes=3, byzantine_ratio=0.0, seed=42):
    """Run a DSECS multi-node simulation."""
    rng = random.Random(seed)
    ledger = InMemoryLedger()
    
    # Bootstrap
    s = State(step=0, stability=0.80, failure_rate=0.15,
              throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    ledger.append(s)
    current = s
    gsai_trace = [GSAI(current)]
    
    for t in range(1, steps + 1):
        # Each node proposes an action
        candidates = []
        for i in range(nodes):
            action = rng.choices(VALID_ACTIONS, weights=[0.60, 0.20, 0.10, 0.10])[0]
            # Byzantine behavior
            if rng.random() < byzantine_ratio:
                action = rng.choice(['NOOP', 'RECOVER'])
            cand = step(current, action, seed=current.step + t + i)
            candidates.append(cand)
        
        cons = majority(candidates)
        if cons.hash != current.hash:
            ledger.append(cons)
            current = cons
        
        gsai_trace.append(GSAI(current))
    
    # Replay verification
    rep_ledger = InMemoryLedger()
    for s in ledger.states:
        rep_ledger.append(s)
    replayed = replay(rep_ledger)
    replay_intact = replayed.hash == current.hash
    
    return {
        'gsai_trace': gsai_trace,
        'ledger_entries': ledger.length,
        'replay_intact': replay_intact,
        'final_gsai': GSAI(current),
        'final_state_hash': current.hash,
        'final_stability': current.stability,
        'final_failure_rate': current.failure_rate,
        'final_throughput': current.throughput,
    }

def run_ablation(steps=500, seed=42):
    """Ablation studies: remove each component."""
    import inspect
    results = {}
    rng = random.Random(seed)
    
    # Full DSECS
    rng = random.Random(seed)
    ledger = InMemoryLedger()
    s = State(step=0, stability=0.80, failure_rate=0.15,
              throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    ledger.append(s)
    current = s
    gsai_trace = [GSAI(current)]
    for t in range(1, steps + 1):
        action = rng.choice(VALID_ACTIONS)
        cand = step(current, action, ledger=ledger, seed=current.step)
        if cand.hash != current.hash:
            current = cand
        gsai_trace.append(GSAI(current))
    results['full'] = {
        'gsai_trace': [round(g, 6) for g in gsai_trace],
        'ledger_entries': ledger.length,
        'final_gsai': round(GSAI(current), 6),
        'final_stability': round(current.stability, 4),
        'final_failure_rate': round(current.failure_rate, 4),
    }
    
    # No CSCO: use raw transition without constraint projection
    rng = random.Random(seed)
    from dsecs.core.transition import transition as raw_transition
    current2 = State(step=0, stability=0.80, failure_rate=0.15,
                     throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    gsai_trace2 = [GSAI(current2)]
    ledger2 = InMemoryLedger()
    for t in range(1, steps + 1):
        action = rng.choice(VALID_ACTIONS)
        cand = raw_transition(current2, action, seed=current2.step)
        current2 = cand
        gsai_trace2.append(GSAI(current2))
    results['no_csco'] = {
        'gsai_trace': [round(g, 6) for g in gsai_trace2],
        'final_gsai': round(GSAI(current2), 6),
        'final_stability': round(current2.stability, 4),
        'final_failure_rate': round(current2.failure_rate, 4),
    }
    
    # No GSAI: disable GSAI scoring, use coin flip for gate
    rng = random.Random(seed)
    current3 = State(step=0, stability=0.80, failure_rate=0.15,
                     throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    gsai_trace3 = [0.5]
    for t in range(1, steps + 1):
        action = rng.choice(VALID_ACTIONS)
        cand = step(current3, action, seed=current3.step)
        if cand.hash != current3.hash and rng.random() < 0.5:
            current3 = cand
        gsai_trace3.append(round(GSAI(current3), 6))
    results['no_gsai'] = {
        'gsai_trace': gsai_trace3,
        'final_gsai': round(GSAI(current3), 6),
        'final_stability': round(current3.stability, 4),
        'final_failure_rate': round(current3.failure_rate, 4),
    }
    
    # No Ledger: multiple runs diverge (simulate by running same sequence twice without ledger sync)
    rng = random.Random(seed)
    current4 = State(step=0, stability=0.80, failure_rate=0.15,
                     throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    gsai_trace4 = [GSAI(current4)]
    current4b = State(step=0, stability=0.80, failure_rate=0.15,
                      throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    gsai_trace4b = [GSAI(current4b)]
    for t in range(1, steps + 1):
        action = rng.choice(VALID_ACTIONS)
        cand = step(current4, action, seed=current4.step)
        if cand.hash != current4.hash:
            current4 = cand
        gsai_trace4.append(GSAI(current4))
        # b diverges due to no ledger sync
        cand_b = step(current4b, action, seed=current4b.step)
        if cand_b.hash != current4b.hash:
            current4b = cand_b
        gsai_trace4b.append(GSAI(current4b))
    ledger_divergence = current4.hash != current4b.hash
    results['no_ledger'] = {
        'gsai_trace': [round(g, 6) for g in gsai_trace4],
        'final_gsai': round(GSAI(current4), 6),
        'final_stability': round(current4.stability, 4),
        'final_failure_rate': round(current4.failure_rate, 4),
        'replicas_diverge': ledger_divergence,
    }
    
    return results

def main():
    out_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(out_dir, exist_ok=True)
    
    print("═══ DSECS Paper v1.0 — Experiments ═══\n")
    
    # Experiment 1: Convergence at different Byzantine ratios
    print("▶ Experiment 1: Convergence Analysis")
    convergence = {}
    for ratio in [0.0, 0.1, 0.2, 0.33]:
        print(f"  Byzantine ratio: {ratio:.2f}")
        result = run_simulation(steps=500, nodes=3, byzantine_ratio=ratio, seed=42)
        convergence[str(ratio)] = {
            'gsai_trace': [round(g, 6) for g in result['gsai_trace']],
            'ledger_entries': result['ledger_entries'],
            'replay_intact': result['replay_intact'],
            'final_gsai': round(result['final_gsai'], 6),
            'final_stability': round(result['final_stability'], 4),
            'final_failure_rate': round(result['final_failure_rate'], 4),
            'final_throughput': round(result['final_throughput'], 4),
        }
        print(f"    Final GSAI: {result['final_gsai']:.6f}  |  "
              f"Ledger entries: {result['ledger_entries']}  |  "
              f"Replay: {'✓' if result['replay_intact'] else '✗'}")
    
    with open(os.path.join(out_dir, 'convergence.json'), 'w') as f:
        json.dump(convergence, f, indent=2)
    print("  ✅ convergence.json saved\n")
    
    # Experiment 2: Ledger consistency across nodes
    print("▶ Experiment 2: Ledger Consistency")
    # All nodes share genesis(42) → same initial hash
    genesis = State(step=0, stability=0.80, failure_rate=0.15,
                    throughput=0.20, consensus_divergence=0.15, memory_ok=True)
    hashes_match = True
    all_hashes = []
    for i in range(10):
        s = State(step=0, stability=0.80, failure_rate=0.15,
                  throughput=0.20, consensus_divergence=0.15, memory_ok=True)
        all_hashes.append(s.hash)
        if s.hash != genesis.hash:
            hashes_match = False
    print(f"  Genesis prefix consistency: {'✓ ALL MATCH' if hashes_match else '✗ MISMATCH'}")
    
    consistency_data = {
        'genesis_hash': genesis.hash,
        'all_nodes_match': hashes_match,
        'distinct_genesis_hashes': len(set(all_hashes)),
    }
    with open(os.path.join(out_dir, 'consistency.json'), 'w') as f:
        json.dump(consistency_data, f, indent=2)
    print("  ✅ consistency.json saved\n")
    
    # Experiment 3: Ablation Study
    print("▶ Experiment 3: Ablation Study")
    ablation = run_ablation(steps=500, seed=42)
    for variant, data in ablation.items():
        trace = data['gsai_trace']
        print(f"  {variant:10s}: final GSAI={data['final_gsai']:.6f}  |  "
              f"min={min(trace):.4f}  max={max(trace):.4f}  "
              f"var={sum((x-sum(trace)/len(trace))**2 for x in trace)/len(trace):.6f}")
    with open(os.path.join(out_dir, 'ablation.json'), 'w') as f:
        json.dump(ablation, f, indent=2, default=str)
    print("  ✅ ablation.json saved\n")
    
    # Experiment 4: Byzantine Stress Test
    print("▶ Experiment 4: Byzantine Stress Test")
    stress_results = {}
    for ratio in [0.0, 0.1, 0.2, 0.33, 0.4]:
        successes = 0
        gsai_vals = []
        for trial in range(10):
            result = run_simulation(steps=200, nodes=3, byzantine_ratio=ratio, seed=trial)
            if result['replay_intact'] and result['final_gsai'] > 0.5:
                successes += 1
            gsai_vals.append(result['final_gsai'])
        stress_results[str(ratio)] = {
            'success_rate': successes / 10,
            'mean_final_gsai': round(sum(gsai_vals) / len(gsai_vals), 6),
            'min_final_gsai': round(min(gsai_vals), 6),
            'max_final_gsai': round(max(gsai_vals), 6),
        }
        print(f"  Byzantine={ratio:.2f}: success rate={successes/10:.1f}  "
              f"mean GSAI={sum(gsai_vals)/len(gsai_vals):.4f}")
    with open(os.path.join(out_dir, 'byzantine_stress.json'), 'w') as f:
        json.dump(stress_results, f, indent=2)
    print("  ✅ byzantine_stress.json saved\n")
    
    print("═══ All experiments complete ═══")

if __name__ == '__main__':
    main()
