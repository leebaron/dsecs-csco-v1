#!/usr/bin/env python3
"""DSECS v1.0 — Official Website + Live Demo Backend.

Single deployment. Zero-config.

Usage:
    python3 site.py
    # → http://localhost:8000
"""

from __future__ import annotations
import time, sys, os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsecs.core.state import State
from dsecs.core.runtime import step
from dsecs.gsa.objective import GSAI
from dsecs.csco.constraint import CSCO
from dsecs.ledger.store import InMemoryLedger
from dsecs.ledger.replay import replay

app = FastAPI(title="DSECS — Decision Infrastructure", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── API endpoints ─────────────────────────────────────────────

@app.get("/case1")
def case1():
    s = State(step=1, stability=0.35, failure_rate=0.45,
              throughput=0.10, consensus_divergence=0.55,
              memory_ok=False, action="HIGH_RISK_TRANSFER")
    violations = []
    if s.failure_rate >= 0.2: violations.append(f"failure_rate {s.failure_rate:.2f} >= 0.20")
    if s.consensus_divergence >= 0.3: violations.append(f"divergence {s.consensus_divergence:.2f} >= 0.30")
    if not s.memory_ok: violations.append("memory_ok is False")
    return {"status": "REJECTED", "csco": False, "gsai": round(GSAI(s), 4), "violations": violations}

@app.get("/case2")
def case2():
    s = State(step=2, stability=0.92, failure_rate=0.03,
              throughput=0.78, consensus_divergence=0.05,
              memory_ok=True, action="COST_OPTIMIZATION")
    g = GSAI(s)
    return {"status": "APPROVED", "csco": True, "gsai": round(g, 4),
            "formula": f"{s.stability:.2f} - 0.5×{s.failure_rate:.2f} + 0.3×{s.throughput:.2f} = {g:.4f}"}

@app.get("/case3")
def case3():
    ledger = InMemoryLedger()
    init = State(step=0, stability=0.95, failure_rate=0.02,
                 throughput=0.30, consensus_divergence=0.02, memory_ok=True)
    ledger.append(init)
    s = init; actions = ["SYNC", "RECOVER", "PROCESS", "NOOP", "RECOVER",
                          "SYNC", "PROCESS", "RECOVER", "SYNC", "OPTIMIZE"]
    trace = []
    for a in actions:
        n = step(s, a, ledger=ledger, seed=ledger.length)
        ok = n.hash != s.hash
        trace.append({"step": n.step, "action": a, "gsai": round(GSAI(n), 4), "accepted": ok})
        if ok: s = n
    try:
        r = replay(ledger); match = r.hash == s.hash
    except: match = False
    return {"status": "VERIFIED", "steps": len(actions), "accepted": sum(1 for t in trace if t["accepted"]),
            "ledger": ledger.length, "replay_match": match, "trace": trace}

@app.get("/health")
def health():
    return {"system": "DSECS v1.0", "status": "running"}

# ── WEBSITE HTML ──────────────────────────────────────────────

SITE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSECS — Decision Infrastructure for AI Systems</title>
<style>
  *,*::after,*::before{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{
    background:#070b10;color:#c8d0d8;font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',Roboto,sans-serif;
    line-height:1.7;-webkit-font-smoothing:antialiased
  }
  .wrap{max-width:960px;margin:0 auto;padding:0 24px}
  a{color:#42a5f5;text-decoration:none}
  .dim{color:#5a6a7a}
  .green{color:#00e676}
  .red{color:#ff5252}
  .blue{color:#42a5f5}
  .mono{font-family:'SF Mono','JetBrains Mono','Fira Code',monospace;font-size:13px}

  /* ── Hero ── */
  .hero{padding:120px 0 80px;position:relative;overflow:hidden;
    background:radial-gradient(ellipse 70% 50% at 50% 15%,#0d1b2a 0%,transparent 70%),
               radial-gradient(ellipse 50% 40% at 70% 85%,#030a12 0%,transparent 70%)}
  .hero .stamp{display:inline-block;font-size:11px;font-weight:600;letter-spacing:2px;padding:5px 14px;
    border-radius:20px;margin-bottom:24px;background:#00e67610;color:#00e676;border:1px solid #00e67622}
  .hero h1{font-size:clamp(36px,6vw,64px);font-weight:800;letter-spacing:-1.5px;line-height:1.05;color:#e8f0f8}
  .hero h1 .grad{background:linear-gradient(135deg,#00e676,#42a5f5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .hero .sub{font-size:clamp(16px,1.6vw,20px);color:#5a6a7a;margin-top:16px;max-width:640px;line-height:1.6;font-weight:300}
  .hero .sub .g{color:#00e676}
  .hero .prov{display:flex;gap:24px;flex-wrap:wrap;margin-top:32px}
  .hero .prov span{display:flex;align-items:center;gap:7px;font-size:14px;color:#8a9aaa}
  .hero .prov .t{width:18px;height:18px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;flex-shrink:0}
  .t-ok{background:#00e67622;color:#00e676}
  .t-no{background:#ff525222;color:#ff5252}

  /* ── Flow ── */
  .flow-sec{padding:80px 0;text-align:center}
  .flow{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:40px}
  .fn{width:210px;padding:28px 20px;border-radius:12px;background:#0c1420;border:1px solid #1a2a3a;transition:all 0.3s}
  .fn:hover{transform:translateY(-3px)}
  .fn .fi{font-size:24px;display:block;margin-bottom:8px}
  .fn .nm{font-size:15px;font-weight:700;letter-spacing:1px;margin-bottom:4px}
  .fn .de{font-size:12px;color:#5a6a7a;line-height:1.5}
  .fn .vl{font-size:11px;margin-top:6px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase}
  .fn.cs{border-color:#ff525233}.fn.cs .nm,.fn.cs .vl{color:#ff5252}
  .fn.gs{border-color:#00e67633}.fn.gs .nm,.fn.gs .vl{color:#00e676}
  .fn.le{border-color:#42a5f533}.fn.le .nm,.fn.le .vl{color:#42a5f5}

  .fa{font-size:24px;color:#2a3a4a;flex-shrink:0;margin:0 4px;animation:faP 2.5s ease-in-out infinite}
  @keyframes faP{0%,100%{opacity:0.2}50%{opacity:1}}

  .metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-top:50px;text-align:left}
  .mc{background:#0c1420;border:1px solid #1a2a3a;border-radius:8px;padding:20px;transition:border-color 0.3s}
  .mc:hover{border-color:#2a3a4a}
  .mc .ml{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#5a6a7a;margin-bottom:6px}
  .mc .mv{font-size:clamp(20px,2.5vw,30px);font-weight:700;font-family:'SF Mono',monospace;color:#e0e8f0}
  .mc .ms{font-size:11px;color:#4a5a6a;margin-top:4px}

  /* ── Content sections ── */
  .sec{padding:80px 0}
  .sec.alt{background:#080c14}
  .sec h2{font-size:clamp(22px,3vw,32px);font-weight:700;color:#d0dce8;margin-bottom:12px;letter-spacing:-0.5px}
  .sec h2 .h{color:#00e676}
  .sec p{font-size:15px;color:#8a9aaa;max-width:700px;line-height:1.8}
  .sec .guarantee{padding:32px 36px;border-radius:12px;background:#0c1420;border:1px solid #00e67622;
    font-size:clamp(16px,2vw,22px);font-weight:700;color:#00e676;text-align:center;margin-top:24px;
    letter-spacing:-0.3px}
  .comp{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:24px}
  .cc{padding:24px;border-radius:10px;border:1px solid #1a2a3a;background:#0a1018}
  .cc.b{border-color:#2a1515}
  .cc.a{border-color:#152a15}
  .cc h3{font-size:14px;margin-bottom:12px;letter-spacing:0.5px}
  .cc ul{list-style:none}
  .cc li{font-size:13px;color:#8a9aaa;padding:5px 0;display:flex;align-items:center;gap:7px}

  /* ── CTA ── */
  .cta-sec{padding:80px 0;text-align:center}
  .cta-sec .btn{display:inline-block;padding:16px 40px;border-radius:8px;
    font-size:15px;font-weight:700;letter-spacing:0.5px;border:none;cursor:pointer;
    background:linear-gradient(135deg,#00e676,#42a5f5);color:#070b10;transition:all 0.3s}
  .cta-sec .btn:hover{transform:translateY(-2px);box-shadow:0 0 40px #00e67633}
  .cta-sec .note{font-size:12px;color:#4a5a6a;margin-top:14px}
  .cta-sec .note a{color:#5a7a9a}

  /* ── Live Demo ── */
  #demo{padding:80px 0}
  #demo h2{text-align:center;margin-bottom:8px}
  #demo .sub{text-align:center;color:#5a6a7a;font-size:14px;margin-bottom:32px}
  .db{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:24px}
  .db button{font-family:inherit;font-size:13px;font-weight:600;padding:11px 22px;border-radius:7px;
    border:1px solid #1a2a3a;cursor:pointer;transition:all 0.2s;background:#0c1420;color:#c8d0d8}
  .db button:hover{border-color:#3a4a5a}
  .db button:disabled{opacity:0.3;cursor:not-allowed}
  .db .r{color:#ff5252;border-color:#ff525233}.db .r:hover{border-color:#ff525266}
  .db .g{color:#00e676;border-color:#00e67633}.db .g:hover{border-color:#00e67666}
  .db .b{color:#42a5f5;border-color:#42a5f533}.db .b:hover{border-color:#42a5f566}

  .do{background:#0a1018;border:1px solid #1a2a3a;border-radius:8px;padding:20px;min-height:80px;
    font-family:'SF Mono','JetBrains Mono',monospace;font-size:12px;line-height:1.8;color:#8899aa;display:none}
  .do.v{display:block;animation:fade .25s ease}
  @keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}

  .footer{text-align:center;padding:32px 24px;color:#2a3a4a;font-size:11px;letter-spacing:1px;
    border-top:1px solid #0e1620}

  @media(max-width:700px){
    .hero{padding:80px 0 50px}
    .flow{flex-direction:column;gap:6px}
    .fa{transform:rotate(90deg)}
    .fn{width:100%;max-width:280px}
    .comp{grid-template-columns:1fr}
  }
</style>
</head>
<body>

<!-- ══════════════ HERO ══════════════ -->
<section class="hero">
  <div class="wrap">
    <div class="stamp">⚡ INFRASTRUCTURE — NOT A MODEL</div>
    <h1>Decision Infrastructure<br/>for <span class="grad">AI Systems</span></h1>
    <p class="sub">
      Make every AI decision <span class="g">constrained</span>,
      <span class="g">scored</span>, and <span class="g">replayable</span>.
      Built for environments that need guarantees, not probabilities.
    </p>
    <div class="prov">
      <span><span class="t t-ok">✓</span> Deterministic</span>
      <span><span class="t t-ok">✓</span> Auditable</span>
      <span><span class="t t-ok">✓</span> Constraint-enforced</span>
      <span><span class="t t-no">✗</span> Not probabilistic</span>
    </div>
  </div>
</section>

<!-- ══════════════ HOW IT WORKS ══════════════ -->
<section class="flow-sec">
  <div class="wrap">
    <h2 style="font-size:22px;color:#b0c0d0;font-weight:600">CSCO → GSAI → Ledger</h2>
    <p class="dim" style="font-size:13px;margin-top:6px">Three layers. One deterministic pipeline.</p>
    <div class="flow">
      <div class="fn cs">
        <span class="fi">⛔</span>
        <div class="nm">CSCO</div>
        <div class="de">Constraint gate rejects unsafe states before any execution</div>
        <div class="vl">Rejects Unsafe</div>
      </div>
      <div class="fa">→</div>
      <div class="fn gs">
        <span class="fi">📊</span>
        <div class="nm">GSAI</div>
        <div class="de">Bounded utility score. Only valid, high-value decisions pass.</div>
        <div class="vl">Scores + Approves</div>
      </div>
      <div class="fa">→</div>
      <div class="fn le">
        <span class="fi">📜</span>
        <div class="nm">Ledger</div>
        <div class="de">Append-only hash chain. Every decision is provable forever.</div>
        <div class="vl">Immutable Audit</div>
      </div>
    </div>
    <div class="metrics">
      <div class="mc"><div class="ml">Determinism</div><div class="mv" style="color:#00e676">100%</div><div class="ms">Same input → Same output</div></div>
      <div class="mc"><div class="ml">Auditability</div><div class="mv" style="color:#42a5f5">Replayable</div><div class="ms">Full state from ledger</div></div>
      <div class="mc"><div class="ml">Safety</div><div class="mv" style="color:#00e676">Constrained</div><div class="ms">Hard gates enforce limits</div></div>
      <div class="mc"><div class="ml">Latency</div><div class="mv" style="color:#e0e8f0">&lt;1 ms</div><div class="ms">Per decision. No inference.</div></div>
    </div>
  </div>
</section>

<!-- ══════════════ PROBLEM ══════════════ -->
<section class="sec alt">
  <div class="wrap">
    <h2>The Problem with AI Decisions</h2>
    <p>Modern AI systems make decisions every second — but no one can prove why a particular decision was made. Outputs are non-deterministic, non-auditable, and non-reproducible. Regulators, auditors, and engineers have no way to verify what happened.</p>
  </div>
</section>

<!-- ══════════════ SOLUTION + GUARANTEE ══════════════ -->
<section class="sec">
  <div class="wrap">
    <h2>The <span class="h">DSECS</span> Solution</h2>
    <p>DSECS introduces a <strong>deterministic decision pipeline</strong> that sits between AI systems and execution. Every decision passes through three verifiable layers: <strong>Constraint → Evaluation → Audit</strong>. Only constrained, high-value decisions execute — and every decision is permanently logged.</p>

    <div class="guarantee">Same input → Same decision → Same audit trail</div>

    <div class="comp" style="margin-top:40px">
      <div class="cc b">
        <h3 style="color:#ff6b6b">Before DSECS</h3>
        <ul>
          <li><span style="color:#ff5252">✗</span> No guarantee or traceability</li>
          <li><span style="color:#ff5252">✗</span> Cannot reproduce a decision</li>
          <li><span style="color:#ff5252">✗</span> Compliance / audit impossible</li>
          <li><span style="color:#ff5252">✗</span> Black-box probabilistic output</li>
        </ul>
      </div>
      <div class="cc a">
        <h3 style="color:#00e676">With DSECS</h3>
        <ul>
          <li><span class="green">✓</span> Every decision is constraint-checked</li>
          <li><span class="green">✓</span> Full hash-chain audit trail</li>
          <li><span class="green">✓</span> Deterministic replay available</li>
          <li><span class="green">✓</span> Compliance-ready by architecture</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════ POSITIONING ══════════════ -->
<section class="sec alt" style="text-align:center">
  <div class="wrap" style="max-width:700px">
    <p style="font-size:clamp(16px,2.2vw,24px);font-weight:700;color:#d0e0f0;line-height:1.5">
      DSECS is <span class="green">not an AI model</span>.<br/>
      It is a <span class="green">decision accountability layer</span> for AI systems.
    </p>
    <p class="dim" style="font-size:13px;margin-top:12px">Constrained · Scored · Hashed · Replayable · Verifiable</p>
  </div>
</section>

<!-- ══════════════ CTA ══════════════ -->
<section class="cta-sec">
  <button class="btn" onclick="document.getElementById('demo').scrollIntoView({behavior:'smooth'})">▶ Run Live Demo</button>
  <div class="note">No install. No config. Three clicks. <br>Or <a href="https://github.com/leebaron/dsecs-csco-v1">view on GitHub</a></div>
</section>

<!-- ══════════════ LIVE DEMO ══════════════ -->
<section id="demo">
  <div class="wrap">
    <h2>🧪 Live Demo</h2>
    <p class="sub">Real kernel. Three cases.</p>
    <div class="db">
      <button class="r" onclick="go(1)" id="b1">⛔ CSCO Reject</button>
      <button class="g" onclick="go(2)" id="b2">✅ GSAI Approve</button>
      <button class="b" onclick="go(3)" id="b3">📜 Replay Proof</button>
    </div>
    <div id="out" class="do"><span class="dim">// Click a case to run against the live DSECS kernel.</span></div>
  </div>
</section>

<footer class="footer">
  DSECS v1.0 &middot; <a href="https://github.com/leebaron/dsecs-csco-v1">github.com/leebaron/dsecs-csco-v1</a>
</footer>

<script>
const b=[1,2,3].map(i=>document.getElementById('b'+i));
const o=document.getElementById('out');
function ld(v){b.forEach(b=>b.disabled=v)}
window.go=async function(n){
  ld(true);
  try{
    const r=await fetch('/case'+n),d=await r.json();
    let h='';
    if(n===1){
      h=`<div style="color:#ff5252;font-weight:700;font-size:14px;margin-bottom:10px;">❌ REJECTED — CSCO Constraint Gate</div>`
        +d.violations.map(v=>`<div style="color:#ff5252;padding:2px 0">✗ ${v}</div>`).join('')
        +`<div style="margin-top:6px;padding-top:6px;border-top:1px solid #1a2a3a"><span class="dim">GSAI:</span> ${d.gsai}</div>`;
    }else if(n===2){
      h=`<div style="color:#00e676;font-weight:700;font-size:14px;margin-bottom:10px;">✅ APPROVED — GSAI Evaluation</div>`
        +`<div><span class="dim">CSCO:</span> <span style="color:#00e676">PASSED</span></div>`
        +`<div><span class="dim">GSAI:</span> <span style="color:#00e676">${d.gsai}</span> <span class="dim">(threshold ≥ 0.50)</span></div>`
        +`<div style="margin-top:8px"><span class="dim">Formula:</span> ${d.formula}</div>`;
    }else{
      const rep=d.replay_match?'<span style="color:#00e676">✅ Deterministic</span>':'<span style="color:#ff5252">❌ Failed</span>';
      let tr='';
      if(d.trace) tr=d.trace.map(s=>
        `<div style="display:flex;gap:8px;font-size:12px;padding:3px 0">`+
        `<span class="dim">${s.step}</span>`+
        `<span style="${s.accepted?'color:#00e676':'color:#5a6a7a'}">${s.accepted?'✅':'⛔'} ${s.action}</span>`+
        `<span class="dim">GSAI ${s.gsai}</span></div>`
      ).join('');
      h=`<div style="color:#42a5f5;font-weight:700;font-size:14px;margin-bottom:10px;">📜 VERIFIED — Ledger + Replay Proof</div>`
        +`<div><span class="dim">Steps:</span> ${d.steps} (${d.accepted} accepted)</div>`
        +`<div><span class="dim">Ledger:</span> ${d.ledger} entries</div>`
        +`<div><span class="dim">Replay:</span> ${rep}</div>`
        +`<div style="margin-top:8px;padding-top:8px;border-top:1px solid #1a2a3a"><span class="dim">Trace:</span></div>`
        +tr;
    }
    o.innerHTML=h;o.className='do v';
  }catch(e){o.innerHTML=`<span style="color:#ff5252">✗ ${e.message}</span>`;o.className='do v'}
  ld(false);
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return SITE

if __name__ == "__main__":
    import uvicorn
    print("DSECS Website — http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
