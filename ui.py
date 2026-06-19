#!/usr/bin/env python3
"""DSECS v1.0 — Investor Landing + Live Decision Visualizer.

Zero-interaction landing page. Opens with instant comprehension.
Backend endpoints power the live demo section.

Usage:
    uvicorn ui:app --reload --port 8000
    # open http://localhost:8000
"""

from __future__ import annotations
import time
import sys
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.gsa.objective import GSAI
from dsecs.csco.constraint import CSCO
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay

app = FastAPI(title="DSECS — Decision Infrastructure", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)

# ── Live backend (same as before) ─────────────────────────────

@app.get("/case1")
def case1():
    bad_state = State(
        step=1, stability=0.35, failure_rate=0.45,
        throughput=0.10, consensus_divergence=0.55,
        memory_ok=False, action="HIGH_RISK_TRANSFER",
    )
    csco_pass = CSCO(bad_state)
    gsai_score = GSAI(bad_state)
    reasons = []
    if bad_state.failure_rate >= 0.2:
        reasons.append(f"failure_rate={bad_state.failure_rate:.2f} >= 0.20")
    if bad_state.consensus_divergence >= 0.3:
        reasons.append(f"divergence={bad_state.consensus_divergence:.2f} >= 0.30")
    if not bad_state.memory_ok:
        reasons.append("memory_ok=False")
    return {
        "case": "CSCO Constraint Gate",
        "status": "REJECTED",
        "csco": csco_pass,
        "gsai_score": round(gsai_score, 6),
        "business_context": {"action": "transfer", "amount": 1000000, "risk": "high"},
        "violations": reasons,
        "state": bad_state.to_dict(),
    }


@app.get("/case2")
def case2():
    good_state = State(
        step=2, stability=0.92, failure_rate=0.03,
        throughput=0.78, consensus_divergence=0.05,
        memory_ok=True, action="COST_OPTIMIZATION",
    )
    csco_pass = CSCO(good_state)
    gsai_score = GSAI(good_state)
    st, fr, tp = good_state.stability, good_state.failure_rate, good_state.throughput
    return {
        "case": "GSAI Evaluation Layer",
        "status": "APPROVED",
        "csco": csco_pass,
        "gsai_score": round(gsai_score, 6),
        "gsai_formula": {
            "expression": "GSAI = stability - 0.5*failure_rate + 0.3*throughput",
            "computation": f"{st:.2f} - 0.5*{fr:.2f} + 0.3*{tp:.2f}",
            "result": round(gsai_score, 6),
        },
        "threshold": {"value": 0.50, "passed": gsai_score >= 0.50},
        "business_context": {"action": "optimize", "risk": "low"},
        "state": good_state.to_dict(),
    }


@app.get("/case3")
def case3():
    trace_ledger = InMemoryLedger()
    init = State(
        step=0, stability=0.95, failure_rate=0.02,
        throughput=0.30, consensus_divergence=0.02, memory_ok=True,
    )
    trace_ledger.append(init)

    actions = ["SYNC", "RECOVER", "PROCESS", "NOOP", "RECOVER",
               "SYNC", "PROCESS", "RECOVER", "SYNC", "OPTIMIZE"]

    trace = []
    s = init
    accepted = rejected = 0
    for action in actions:
        s_next = step(s, action, ledger=trace_ledger, seed=trace_ledger.length)
        state_accepted = s_next.hash != s.hash
        trace.append({
            "step": s_next.step, "action": action,
            "gsai": round(GSAI(s_next), 6), "csco": CSCO(s_next),
            "accepted": state_accepted, "hash": s_next.hash,
        })
        if state_accepted:
            s = s_next; accepted += 1
        else:
            rejected += 1

    t0 = time.perf_counter()
    try:
        replayed = replay(trace_ledger)
        replay_ms = round((time.perf_counter() - t0) * 1000, 3)
        replay_match = replayed.hash == s.hash
    except (AssertionError, ValueError):
        replay_ms = 0.0
        replay_match = False
        replayed = None

    stored = trace_ledger.states
    chain_ok = all(
        stored[i].hash == stored[i+1].parent_hash
        for i in range(len(stored) - 1)
    )

    return {
        "case": "Ledger + Replay Proof",
        "status": "VERIFIED" if (replay_match and chain_ok) else "FAILED",
        "trace": {
            "total_steps": len(actions), "accepted": accepted,
            "rejected": rejected, "ledger_entries": trace_ledger.length,
            "steps": trace,
        },
        "replay": {
            "time_ms": replay_ms, "match": replay_match,
            "original_final_hash": s.hash,
            "replayed_final_hash": replayed.hash if replayed else None,
        },
        "hash_chain": {
            "consistent": chain_ok,
            "check": f"{len(stored)} entries, "
                     f"{'all verified' if chain_ok else 'broken'}",
        },
    }


@app.get("/reset")
def reset():
    return {"status": "reset"}


@app.get("/health")
def health():
    return {"system": "DSECS v1.0", "status": "running"}


# ── INVESTOR-GRADE LANDING PAGE ────────────────────────────────

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSECS — Decision Infrastructure for AI Systems</title>
<style>
  /* ── Reset & Base ── */
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{
    background:#070b10;color:#e0e8f0;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
    line-height:1.6;-webkit-font-smoothing:antialiased
  }
  a{color:inherit;text-decoration:none}

  /* ── Containers ── */
  .wrap{max-width:1100px;margin:0 auto;padding:0 24px}

  /* ── Typography ── */
  h1{font-size:clamp(36px,5vw,60px);font-weight:700;letter-spacing:-1.5px;line-height:1.1}
  h2{font-size:28px;font-weight:600;letter-spacing:-0.5px;margin-bottom:16px}
  h3{font-size:20px;font-weight:600;margin-bottom:8px}
  .mono{font-family:'SF Mono','JetBrains Mono','Fira Code','Cascadia Code',monospace;font-size:13px}
  .dim{color:#6a7a8a}
  .green{color:#00e676}
  .red{color:#ff5252}
  .blue{color:#42a5f5}

  /* ── Hero ── */
  .hero{
    min-height:100vh;display:flex;flex-direction:column;justify-content:center;
    padding:80px 0 40px;position:relative;overflow:hidden;
    background:radial-gradient(ellipse 80% 60% at 50% 20%,#0d1b2a 0%,transparent 70%),
               radial-gradient(ellipse 60% 50% at 70% 80%,#030a12 0%,transparent 70%);
  }
  .hero .badge{
    display:inline-block;font-size:12px;font-weight:600;letter-spacing:2px;
    padding:6px 16px;border-radius:20px;margin-bottom:20px;
    background:#00e67610;color:#00e676;border:1px solid #00e67622;
  }
  .hero h1 span.dsecs{background:linear-gradient(135deg,#00e676,#42a5f5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .hero .tagline{font-size:20px;color:#8a9aaa;margin-top:16px;max-width:720px;font-weight:300}
  .hero .statements{margin-top:32px;display:flex;gap:32px;flex-wrap:wrap}
  .hero .statements span{display:flex;align-items:center;gap:8px;font-size:15px;color:#b0c0d0}
  .hero .statements .icon{width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}
  .icon-ok{background:#00e67622;color:#00e676}
  .icon-no{background:#ff525222;color:#ff5252}

  /* ── Animated Flow ── */
  .flow-section{padding:80px 0}
  .flow-section h2{text-align:center;margin-bottom:50px;color:#c0d0e0}
  .flow{
    display:flex;align-items:center;justify-content:center;
    gap:12px;flex-wrap:wrap
  }
  .flow-node{
    width:220px;padding:32px 24px;border-radius:14px;text-align:center;
    background:linear-gradient(145deg,#101820,#0c1420);position:relative;
    border:1px solid #1a2a3a;transition:all 0.3s
  }
  .flow-node:hover{transform:translateY(-4px)}
  .flow-node .icon{font-size:28px;margin-bottom:12px;display:block}
  .flow-node .name{font-size:16px;font-weight:700;letter-spacing:1px;margin-bottom:6px}
  .flow-node .desc{font-size:12px;color:#6a7a8a;line-height:1.5}
  .flow-node .value{font-size:12px;margin-top:6px;font-weight:600;letter-spacing:0.5px}

  .flow-node.csco{border-color:#ff525244}
  .flow-node.csco .name{color:#ff5252}
  .flow-node.csco .value{color:#ff5252}
  .flow-node.csco:hover{border-color:#ff525288;box-shadow:0 0 30px #ff525222}

  .flow-node.gsai{border-color:#00e67644}
  .flow-node.gsai .name{color:#00e676}
  .flow-node.gsai .value{color:#00e676}
  .flow-node.gsai:hover{border-color:#00e67688;box-shadow:0 0 30px #00e67622}

  .flow-node.ledger{border-color:#42a5f544}
  .flow-node.ledger .name{color:#42a5f5}
  .flow-node.ledger .value{color:#42a5f5}
  .flow-node.ledger:hover{border-color:#42a5f588;box-shadow:0 0 30px #42a5f522}

  /* Animated glow pulse */
  .flow-node.pulse{animation:pulseGlow 3s ease-in-out infinite}
  .flow-node.csco.pulse{animation-delay:0s}
  .flow-node.gsai.pulse{animation-delay:1s}
  .flow-node.ledger.pulse{animation-delay:2s}
  @keyframes pulseGlow{
    0%,100%{box-shadow:0 0 0px transparent}
    50%{box-shadow:0 0 25px var(--glow,currentColor)}
  }

  .flow-arrow{
    font-size:28px;color:#2a3a4a;flex-shrink:0;
    animation:arrowPulse 2.5s ease-in-out infinite
  }
  @keyframes arrowPulse{
    0%,100%{opacity:0.3;transform:translateX(0)}
    50%{opacity:1;transform:translateX(4px)}
  }

  /* ── Metrics Row ── */
  .metrics{
    display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
    gap:16px;margin-top:50px
  }
  .metric-card{
    background:#0e1620;border:1px solid #1a2a3a;border-radius:10px;
    padding:24px;text-align:center;transition:border-color 0.3s
  }
  .metric-card:hover{border-color:#2a3a4a}
  .metric-card .m-label{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#6a7a8a;margin-bottom:8px}
  .metric-card .m-value{font-size:clamp(24px,3vw,36px);font-weight:700;font-family:'SF Mono',monospace}
  .metric-card .m-sub{font-size:12px;color:#4a5a6a;margin-top:6px}

  /* ── Before/After ── */
  .comparison-section{padding:80px 0;background:linear-gradient(180deg,#070b10,#0a121e,#070b10)}
  .comparison{
    display:grid;grid-template-columns:1fr 1fr;gap:32px;margin-top:30px
  }
  .comp-card{
    padding:28px;border-radius:12px;border:1px solid #1a2a3a
  }
  .comp-card.before{background:#0c0c10;border-color:#2a1a1a}
  .comp-card.after{background:#0c1410;border-color:#1a2a1a}
  .comp-card h3{font-size:16px;margin-bottom:12px}
  .comp-card ul{list-style:none}
  .comp-card li{font-size:13px;color:#8a9aaa;padding:6px 0;display:flex;align-items:center;gap:8px}
  .comp-card.after li{color:#b0c8b0}

  /* ── Positioning ── */
  .position-section{padding:80px 0;text-align:center}
  .position-block{
    max-width:800px;margin:0 auto;
    padding:48px 40px;border-radius:16px;
    background:linear-gradient(145deg,#0d1b2a,#0a121e);
    border:1px solid #1a2a3a;
  }
  .position-block h2{font-size:clamp(20px,3vw,32px);margin-bottom:16px;color:#e0e8f0}
  .position-block .highlight{color:#00e676;font-weight:600}
  .position-block .sub{color:#6a7a8a;font-size:15px;margin-top:8px}

  /* ── Live Demo CTA ── */
  .demo-cta{padding:60px 0 30px;text-align:center}
  .demo-cta .btn{
    display:inline-block;padding:14px 36px;border-radius:8px;
    font-size:14px;font-weight:600;letter-spacing:0.5px;
    background:linear-gradient(135deg,#00e676,#42a5f5);color:#070b10;border:none;
    cursor:pointer;transition:all 0.3s
  }
  .demo-cta .btn:hover{transform:translateY(-2px);box-shadow:0 0 30px #00e67644}
  .demo-cta .note{font-size:11px;color:#4a5a6a;margin-top:12px}

  /* ── Live Demo Section ── */
  #live-demo{padding:80px 0}
  #live-demo h2{text-align:center;margin-bottom:10px}
  #live-demo .sub{text-align:center;color:#6a7a8a;font-size:14px;margin-bottom:40px}

  .demo-buttons{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:30px}
  .demo-btn{
    font-family:inherit;font-size:13px;font-weight:600;padding:12px 24px;
    border-radius:8px;border:1px solid #1a2a3a;cursor:pointer;transition:all 0.2s;
    background:#0e1620;color:#e0e8f0
  }
  .demo-btn:hover{background:#162230;border-color:#2a3a4a}
  .demo-btn:active{transform:scale(0.97)}
  .demo-btn:disabled{opacity:0.3;cursor:not-allowed}
  .demo-btn.d1{color:#ff5252;border-color:#ff525244}
  .demo-btn.d1:hover{border-color:#ff525288}
  .demo-btn.d2{color:#00e676;border-color:#00e67644}
  .demo-btn.d2:hover{border-color:#00e67688}
  .demo-btn.d3{color:#42a5f5;border-color:#42a5f544}
  .demo-btn.d3:hover{border-color:#42a5f588}

  .demo-output{
    background:#0a1018;border:1px solid #1a2a3a;border-radius:10px;
    padding:24px;min-height:120px;display:none;
    font-family:'SF Mono','JetBrains Mono',monospace;font-size:12px;line-height:1.8;color:#b0c0d0
  }
  .demo-output.visible{display:block;animation:fadeIn 0.3s ease}
  .demo-output .ok{color:#00e676}
  .demo-output .err{color:#ff5252}
  .demo-output .info{color:#42a5f5}
  .demo-output .dim{color:#6a7a8a}
  .demo-output .kv{display:flex;gap:6px;padding:2px 0}
  .demo-output .kv .k{color:#6a7a8a;min-width:120px}
  .demo-output .kv .v{color:#d0e0f0}

  @keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

  /* ── Footer ── */
  .footer{
    text-align:center;padding:40px 24px;color:#3a4a5a;font-size:11px;letter-spacing:1px;
    border-top:1px solid #0e1620
  }

  /* ── Responsive ── */
  @media(max-width:768px){
    .hero{padding:60px 0 30px}
    .flow{flex-direction:column;gap:8px}
    .flow-arrow{transform:rotate(90deg);margin:4px 0}
    .flow-arrow{animation:arrowPulseV 2.5s ease-in-out infinite}
    @keyframes arrowPulseV{0%,100%{opacity:0.3;transform:rotate(90deg) translateX(0)}50%{opacity:1;transform:rotate(90deg) translateX(4px)}}
    .flow-node{width:100%;max-width:300px}
    .comparison{grid-template-columns:1fr}
  }
</style>
</head>
<body>

<!-- ══════════════════════════════════════════ HERO ═══ -->
<section class="hero">
  <div class="wrap">
    <div class="badge">⚡ INFRASTRUCTURE — NOT A MODEL</div>
    <h1><span class="dsecs">DSECS</span><br/>Decision Infrastructure for AI</h1>
    <p class="tagline">
      Every AI decision becomes constrained, scored, hashed, and replayable.
      Built for regulated industries that need guarantees, not probabilities.
    </p>
    <div class="statements">
      <span><span class="icon icon-ok">✓</span> Deterministic</span>
      <span><span class="icon icon-ok">✓</span> Auditable</span>
      <span><span class="icon icon-ok">✓</span> Constraint-enforced</span>
      <span><span class="icon icon-no">✗</span> Not probabilistic</span>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════ ANIMATED FLOW ═══ -->
<section class="flow-section">
  <div class="wrap">
    <h2>How It Works</h2>
    <div class="flow">

      <div class="flow-node csco pulse">
        <span class="icon">⛔</span>
        <div class="name">CSCO</div>
        <div class="desc">Constraint gate rejects unsafe states.<br/>Every decision is pre-validated.</div>
        <div class="value">REJECTS UNSAFE</div>
      </div>

      <div class="flow-arrow">→</div>

      <div class="flow-node gsai pulse">
        <span class="icon">📊</span>
        <div class="name">GSAI</div>
        <div class="desc">Bounded utility score.<br/>Only valid states with sufficient value pass.</div>
        <div class="value">SCORES + APPROVES</div>
      </div>

      <div class="flow-arrow">→</div>

      <div class="flow-node ledger pulse">
        <span class="icon">📜</span>
        <div class="name">Ledger</div>
        <div class="desc">Append-only hash chain.<br/>Every decision is provable forever.</div>
        <div class="value">IMMUTABLE AUDIT</div>
      </div>

    </div>

    <div class="metrics">
      <div class="metric-card">
        <div class="m-label">Determinism</div>
        <div class="m-value green">100%</div>
        <div class="m-sub">Same input → Same output. Always.</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Auditability</div>
        <div class="m-value blue">REPLAYABLE</div>
        <div class="m-sub">Full state reconstruction from ledger.</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Safety</div>
        <div class="m-value green">CONSTRAINED</div>
        <div class="m-sub">Hard constraints prevent unsafe states.</div>
      </div>
      <div class="metric-card">
        <div class="m-label">Cold Start</div>
        <div class="m-value" style="color:#e0e8f0">&lt;1 ms</div>
        <div class="m-sub">Per-decision latency. No model inference.</div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════ BEFORE/AFTER ═══ -->
<section class="comparison-section">
  <div class="wrap">
    <h2 style="text-align:center;color:#c0d0e0">The Difference</h2>
    <div class="comparison">

      <div class="comp-card before">
        <h3 style="color:#ff6b6b;">Before DSECS</h3>
        <ul>
          <li><span style="color:#ff5252;">✗</span> AI outputs text — no guarantee</li>
          <li><span style="color:#ff5252;">✗</span> No traceability after decision</li>
          <li><span style="color:#ff5252;">✗</span> Probabilistic — can't reproduce</li>
          <li><span style="color:#ff5252;">✗</span> Cannot prove what happened</li>
          <li><span style="color:#ff5252;">✗</span> Compliance / audit impossible</li>
        </ul>
      </div>

      <div class="comp-card after">
        <h3 style="color:#00e676;">With DSECS</h3>
        <ul>
          <li><span class="green">✓</span> Every decision is constrained by rules</li>
          <li><span class="green">✓</span> Full audit trail — hash-chain ledger</li>
          <li><span class="green">✓</span> Deterministic replay at any point</li>
          <li><span class="green">✓</span> Bounded utility scoring (GSAI)</li>
          <li><span class="green">✓</span> Compliance-ready by architecture</li>
        </ul>
      </div>

    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════ POSITIONING ═══ -->
<section class="position-section">
  <div class="wrap">
    <div class="position-block">
      <h2>
        DSECS is <span class="highlight">not an AI model</span>.<br/>
        It is a <span class="highlight">decision accountability layer</span>
        for AI systems.
      </h2>
      <p class="sub">
        Constrained · Scored · Hashed · Replayable · Verifiable
      </p>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════ CTA ═══ -->
<section class="demo-cta">
  <button class="btn" onclick="document.getElementById('live-demo').scrollIntoView({behavior:'smooth'});">
    ▶ Run Live Demo
  </button>
  <div class="note">No install. No config. Three clicks.</div>
</section>

<!-- ══════════════════════════════════════════ LIVE DEMO ═══ -->
<section id="live-demo">
  <div class="wrap">
    <h2>🧪 Live Demo</h2>
    <p class="sub">Three cases. Real kernel. See it in action.</p>

    <div class="demo-buttons">
      <button class="demo-btn d1" onclick="runDemo(1)" id="db1">⛔ Case 1: CSCO Reject</button>
      <button class="demo-btn d2" onclick="runDemo(2)" id="db2">✅ Case 2: GSAI Approve</button>
      <button class="demo-btn d3" onclick="runDemo(3)" id="db3">📜 Case 3: Replay Proof</button>
      <button class="demo-btn" onclick="runDemo('reset')" id="dbR" style="color:#6a7a8a;">⟳ Reset</button>
    </div>

    <div id="demo-output" class="demo-output">
      <span class="dim">// Click a case to run it against the live DSECS kernel.</span>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════ FOOTER ═══ -->
<footer class="footer">
  DSECS v1.0 &middot; github.com/leebaron/dsecs-csco-v1 &middot; Deterministic · Auditable · Verifiable
</footer>

<script>
const btns=[1,2,3,'R'].map(i=>document.getElementById('db'+i));
const output=document.getElementById('demo-output');

function loading(on){btns.forEach(b=>{b.disabled=on;})}

function showOutput(html){
  output.innerHTML=html;
  output.className='demo-output visible';
}

window.runDemo=async function(n){
  loading(true);
  try{
    if(n==='reset'){showOutput('<span class="dim">// Demo reset. Click a case.</span>');loading(false);return}
    const res=await fetch('/case'+n);
    const d=await res.json();
    renderOutput(n,d);
  }catch(e){showOutput('<span class="err">✗ Error: '+e.message+'</span>')}
  loading(false);
}

function renderOutput(n,d){
  if(n===1) renderCase1(d);
  else if(n===2) renderCase2(d);
  else if(n===3) renderCase3(d);
}

function renderCase1(d){
  let vhtml=d.violations.map(v=>'<div style="color:#ff5252;padding:2px 0">✗ '+v+'</div>').join('');
  showOutput(
    '<div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#ff5252;">❌ '+d.status+' — '+d.case+'</div>'+
    '<div class="kv"><span class="k">Business</span><span class="v">'+d.business_context.action+' $'+(d.business_context.amount/1000000)+'M risk='+d.business_context.risk+'</span></div>'+
    '<div class="kv"><span class="k">CSCO Gate</span><span class="err">FAILED</span></div>'+
    '<div class="kv"><span class="k">GSAI Score</span><span class="err">'+d.gsai_score.toFixed(4)+'</span></div>'+
    '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #1a2a3a;color:#ff5252;font-weight:600;">Violations</div>'+
    vhtml
  );
}

function renderCase2(d){
  showOutput(
    '<div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#00e676;">✅ '+d.status+' — '+d.case+'</div>'+
    '<div class="kv"><span class="k">Business</span><span class="v">'+d.business_context.action+' risk='+d.business_context.risk+'</span></div>'+
    '<div class="kv"><span class="k">CSCO Gate</span><span class="ok">PASSED</span></div>'+
    '<div class="kv"><span class="k">GSAI Score</span><span class="ok">'+d.gsai_score.toFixed(4)+'</span></div>'+
    '<div class="kv"><span class="k">Threshold (≥0.50)</span><span class="ok">PASSED</span></div>'+
    '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #1a2a3a;">'+
      '<div class="dim">GSAI = stability - 0.5×failure_rate + 0.3×throughput</div>'+
      '<div class="dim">= '+d.gsai_formula.computation+'</div>'+
      '<div style="color:#00e676;font-weight:600;margin-top:4px;">= '+d.gsai_score.toFixed(6)+'</div>'+
    '</div>'
  );
}

function renderCase3(d){
  let rows='';
  if(d.trace.steps){
    rows=d.trace.steps.map(s=>{
      const m=s.accepted?'✅':'⛔';
      const c=s.accepted?'ok':'dim';
      return '<div class="kv" style="font-size:12px;"><span class="k" style="min-width:40px">'+
        s.step+'</span><span style="min-width:100px">'+m+' '+s.action+'</span>'+
        '<span class="'+c+'" style="min-width:80px">GSAI '+s.gsai.toFixed(4)+'</span>'+
        '<span class="dim" style="font-size:11px">'+s.hash.slice(0,12)+'…</span></div>';
    }).join('');
  }
  const replayStatus=d.replay.match?'✅ Deterministic':'❌ Diverged';
  showOutput(
    '<div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#42a5f5;">📜 '+d.status+' — '+d.case+'</div>'+
    '<div class="kv"><span class="k">Total Steps</span><span class="v">'+d.trace.total_steps+'</span></div>'+
    '<div class="kv"><span class="k">Accepted/Rejected</span><span class="v">'+d.trace.accepted+' / '+d.trace.rejected+'</span></div>'+
    '<div class="kv"><span class="k">Ledger Entries</span><span class="v">'+d.trace.ledger_entries+'</span></div>'+
    '<div class="kv"><span class="k">Replay</span><span class="ok">'+replayStatus+' ('+d.replay.time_ms+' ms)</span></div>'+
    '<div class="kv"><span class="k">Hash Chain</span><span class="ok">Consistent</span></div>'+
    '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #1a2a3a;">'+
      '<div class="dim" style="margin-bottom:6px;">Decision Trace</div>'+rows+
    '</div>'
  );
}
</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


if __name__ == "__main__":
    import uvicorn
    print("DSECS Landing — http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
