#!/usr/bin/env python3
"""
DSECS Enterprise ROI Calculator
================================
Usage (CLI):
    python roi_calculator.py --ai-decision-volume 10000 --avg-decision-value 500

Generates: cost savings, risk reduction, compliance value.
"""

import argparse
import json
import math

# --- Constants (conservative estimates) ---

# Without DSECS
INCIDENT_RATE_NO_GOVERNANCE = 0.015       # 1.5% of decisions cause incidents
AVG_INCIDENT_COST = 250000                # $250K per incident (labor, remediation, fines)
COMPLIANCE_PENALTY_RISK = 0.05            # 5% annual compliance fine risk
AVG_ANNUAL_AUDIT_COST = 180000            # $180K for manual audit
MANUAL_REVIEW_COST_PER_DECISION = 15      # $15/high-risk decision manual review
HIGH_RISK_DECISION_RATE = 0.08            # 8% of decisions flagged high-risk

# With DSECS
DSECS_REDUCED_INCIDENT_RATE = 0.001       # 0.1% incident rate (93% reduction)
DSECS_AUDIT_COST = 24000                  # $24K/year automated audit
DSECS_REVIEW_COST_PER_DECISION = 0.05     # $0.05/decision automated review
DSECS_ANNUAL_LICENSE = 50000              # $50K/year base SaaS


def calculate_roi(volume: int, avg_value: float, compliance_penalty_base: float = 1_000_000):
    """Return a full ROI breakdown for DSECS adoption."""

    # --- Without DSECS ---
    annual_incidents = volume * INCIDENT_RATE_NO_GOVERNANCE
    incident_cost = annual_incidents * AVG_INCIDENT_COST
    incident_loss = avg_value * annual_incidents * 0.5  # avg loss per incident

    # Manual review
    high_risk_decisions = volume * HIGH_RISK_DECISION_RATE
    review_cost = high_risk_decisions * MANUAL_REVIEW_COST_PER_DECISION

    # Compliance
    compliance_risk = compliance_penalty_base * COMPLIANCE_PENALTY_RISK
    audit_cost = AVG_ANNUAL_AUDIT_COST

    total_without = incident_cost + incident_loss + review_cost + compliance_risk + audit_cost

    # --- With DSECS ---
    dsecs_incidents = volume * DSECS_REDUCED_INCIDENT_RATE
    dsecs_incident_cost = dsecs_incidents * AVG_INCIDENT_COST
    dsecs_incident_loss = avg_value * dsecs_incidents * 0.5

    dsecs_review_cost = volume * DSECS_REVIEW_COST_PER_DECISION
    dsecs_compliance_risk = compliance_penalty_base * 0.01  # 1% risk with governance
    dsecs_audit_cost = DSECS_AUDIT_COST
    dsecs_license = DSECS_ANNUAL_LICENSE

    total_with = dsecs_incident_cost + dsecs_incident_loss + dsecs_review_cost + dsecs_compliance_risk + dsecs_audit_cost + dsecs_license

    savings = total_without - total_with
    roi_pct = (savings / total_with) * 100 if total_with > 0 else float("inf")

    return {
        "inputs": {
            "decision_volume_per_year": volume,
            "avg_decision_value": avg_value,
        },
        "without_dsecs": {
            "annual_incidents": round(annual_incidents, 1),
            "incident_direct_cost": round(incident_cost),
            "incident_value_loss": round(incident_loss),
            "manual_review_cost": round(review_cost),
            "compliance_risk_cost": round(compliance_risk),
            "audit_cost": round(audit_cost),
            "total_annual_cost": round(total_without),
        },
        "with_dsecs": {
            "annual_incidents": round(dsecs_incidents, 1),
            "incident_direct_cost": round(dsecs_incident_cost),
            "incident_value_loss": round(dsecs_incident_loss),
            "automated_review_cost": round(dsecs_review_cost),
            "residual_compliance_risk": round(dsecs_compliance_risk),
            "audit_cost": round(dsecs_audit_cost),
            "license_cost": round(dsecs_license),
            "total_annual_cost": round(total_with),
        },
        "net_savings": round(savings),
        "roi_percentage": round(roi_pct, 1),
        "payback_months": round((dsecs_license / savings) * 12, 1) if savings > 0 else 0,
        "metrics": {
            "incident_reduction_pct": round((1 - DSECS_REDUCED_INCIDENT_RATE / max(INCIDENT_RATE_NO_GOVERNANCE, 0.001)) * 100, 1),
            "audit_cost_reduction_pct": round((1 - dsecs_audit_cost / max(audit_cost, 1)) * 100, 1),
            "review_efficiency_multiple": round(MANUAL_REVIEW_COST_PER_DECISION / max(DSECS_REVIEW_COST_PER_DECISION, 0.001), 1),
        },
    }


def main():
    parser = argparse.ArgumentParser("DSECS ROI Calculator")
    parser.add_argument("--volume", type=int, default=10000, help="Annual AI decision volume")
    parser.add_argument("--avg-value", type=float, default=500, help="Average value per decision ($)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--web", action="store_true", help="Generate interactive HTML calculator")
    args = parser.parse_args()

    roi = calculate_roi(args.volume, args.avg_value)

    if args.json:
        print(json.dumps(roi, indent=2))
        return

    if args.web:
        generate_web_calculator()
        return

    print("=" * 60)
    print("DSECS Enterprise ROI Calculator")
    print("=" * 60)
    print(f"\nInputs:")
    print(f"  Annual AI decision volume: {roi['inputs']['decision_volume_per_year']:,}")
    print(f"  Average decision value:    ${roi['inputs']['avg_decision_value']:,.0f}")

    print(f"\n📉 Without DSECS:")
    for k, v in roi["without_dsecs"].items():
        print(f"  {k.replace('_', ' ').title()}: ${v:,.0f}")
    print(f"\n  TOTAL: ${roi['without_dsecs']['total_annual_cost']:,.0f}")

    print(f"\n📈 With DSECS:")
    for k, v in roi["with_dsecs"].items():
        print(f"  {k.replace('_', ' ').title()}: ${v:,.0f}")
    print(f"\n  TOTAL: ${roi['with_dsecs']['total_annual_cost']:,.0f}")

    print(f"\n✅ Net Annual Savings: ${roi['net_savings']:,.0f}")
    print(f"✅ ROI: {roi['roi_percentage']}%")
    print(f"✅ Payback period: {roi['payback_months']} months")
    print(f"✅ Incident reduction: {roi['metrics']['incident_reduction_pct']}%")
    print(f"✅ Audit cost reduction: {roi['metrics']['audit_cost_reduction_pct']}%")
    print(f"✅ Review efficiency: {roi['metrics']['review_efficiency_multiple']}x faster")


def generate_web_calculator():
    """Generate an interactive HTML version."""
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSECS ROI Calculator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, system-ui, sans-serif; background: #f5f5f7; color: #1d1d1f; padding: 40px 20px; display: flex; justify-content: center; }
  .card { max-width: 720px; width: 100%; background: #fff; border-radius: 20px; padding: 40px; box-shadow: 0 2px 20px rgba(0,0,0,0.08); }
  h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
  .sub { color: #6e6e73; font-size: 15px; margin-bottom: 32px; }
  .row { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
  .field { flex: 1; min-width: 200px; }
  label { display: block; font-size: 13px; font-weight: 600; color: #6e6e73; margin-bottom: 4px; }
  input { width: 100%; padding: 12px 16px; border: 1px solid #d2d2d7; border-radius: 12px; font-size: 16px; outline: none; }
  input:focus { border-color: #0071e3; box-shadow: 0 0 0 3px rgba(0,113,227,0.15); }
  button { width: 100%; padding: 14px; background: #0071e3; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 8px 0 32px; }
  button:hover { background: #0065cc; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .metric { background: #f5f5f7; border-radius: 12px; padding: 20px; text-align: center; }
  .metric .val { font-size: 28px; font-weight: 700; color: #0071e3; }
  .metric .lbl { font-size: 13px; color: #6e6e73; margin-top: 4px; }
  .metric.green .val { color: #34c759; }
  .metric.red .val { color: #ff3b30; }
  .section { margin-bottom: 24px; }
  .section h3 { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #6e6e73; }
  .row-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e8e8ed; font-size: 14px; }
  .row-item:last-child { border-bottom: none; font-weight: 700; }
  .row-item .label { color: #1d1d1f; }
  .row-item .value { color: #1d1d1f; }
  .savings { background: #e8f5e9; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 16px; }
  .savings .val { font-size: 36px; font-weight: 700; color: #2e7d32; }
  .savings .lbl { font-size: 14px; color: #388e3c; margin-top: 4px; }
</style>
</head>
<body>
<div class="card">
  <h1>DSECS ROI Calculator</h1>
  <p class="sub">Estimate annual savings by adding runtime governance to your AI decisions.</p>

  <div class="row">
    <div class="field">
      <label>Annual AI Decision Volume</label>
      <input type="number" id="volume" value="10000" min="0" step="1000">
    </div>
    <div class="field">
      <label>Avg Decision Value ($)</label>
      <input type="number" id="avgValue" value="500" min="0" step="100">
    </div>
  </div>

  <button onclick="calculate()">Calculate ROI</button>

  <div id="results" style="display:none">
    <div class="savings">
      <div class="val" id="netSavings">$0</div>
      <div class="lbl">Net Annual Savings</div>
    </div>

    <div class="grid">
      <div class="metric green"><div class="val" id="roiPct">0%</div><div class="lbl">ROI</div></div>
      <div class="metric green"><div class="val" id="payback">0</div><div class="lbl">Payback (months)</div></div>
      <div class="metric green"><div class="val" id="incidentReduction">0%</div><div class="lbl">Incident Reduction</div></div>
      <div class="metric green"><div class="val" id="auditReduction">0%</div><div class="lbl">Audit Cost Reduction</div></div>
    </div>

    <div class="section">
      <h3>Without DSECS</h3>
      <div id="withoutBreakdown"></div>
    </div>

    <div class="section">
      <h3>With DSECS</h3>
      <div id="withBreakdown"></div>
    </div>
  </div>
</div>

<script>
const INCIDENT_RATE_NO = 0.015;
const AVG_INCIDENT_COST = 250000;
const COMPLIANCE_PENALTY_RISK = 0.05;
const AVG_AUDIT_COST = 180000;
const MANUAL_REVIEW_COST = 15;
const HIGH_RISK_RATE = 0.08;
const COMPLIANCE_BASE = 1000000;

const DSECS_INCIDENT_RATE = 0.001;
const DSECS_AUDIT_COST = 24000;
const DSECS_REVIEW_COST = 0.05;
const DSECS_LICENSE = 50000;

function fmt(n) { return "$" + Number(n).toLocaleString("en-US", {maximumFractionDigits:0}); }
function fmtPct(n) { return Number(n).toFixed(1) + "%"; }

function calculate() {
  const volume = parseFloat(document.getElementById("volume").value) || 10000;
  const avgVal = parseFloat(document.getElementById("avgValue").value) || 500;

  const annualIncidents = volume * INCIDENT_RATE_NO;
  const incidentCost = annualIncidents * AVG_INCIDENT_COST;
  const incidentLoss = avgVal * annualIncidents * 0.5;
  const reviewCost = volume * HIGH_RISK_RATE * MANUAL_REVIEW_COST;
  const complianceRisk = COMPLIANCE_BASE * COMPLIANCE_PENALTY_RISK;
  const auditCost = AVG_AUDIT_COST;
  const totalWithout = incidentCost + incidentLoss + reviewCost + complianceRisk + auditCost;

  const dIncidents = volume * DSECS_INCIDENT_RATE;
  const dIncidentCost = dIncidents * AVG_INCIDENT_COST;
  const dIncidentLoss = avgVal * dIncidents * 0.5;
  const dReviewCost = volume * DSECS_REVIEW_COST;
  const dComplianceRisk = COMPLIANCE_BASE * 0.01;
  const dAuditCost = DSECS_AUDIT_COST;
  const dLicense = DSECS_LICENSE;
  const totalWith = dIncidentCost + dIncidentLoss + dReviewCost + dComplianceRisk + dAuditCost + dLicense;

  const savings = totalWithout - totalWith;
  const roi = savings > 0 ? (savings / totalWith) * 100 : 0;
  const payback = savings > 0 ? (dLicense / savings) * 12 : 0;
  const incRed = (1 - DSECS_INCIDENT_RATE / INCIDENT_RATE_NO) * 100;
  const auditRed = (1 - dAuditCost / AVG_AUDIT_COST) * 100;

  document.getElementById("netSavings").textContent = fmt(savings);
  document.getElementById("roiPct").textContent = fmtPct(roi);
  document.getElementById("payback").textContent = payback.toFixed(1);
  document.getElementById("incidentReduction").textContent = fmtPct(incRed);
  document.getElementById("auditReduction").textContent = fmtPct(auditRed);

  const withoutItems = [
    ["Annual incidents", annualIncidents.toFixed(1)],
    ["Incident direct cost", fmt(incidentCost)],
    ["Incident value loss", fmt(incidentLoss)],
    ["Manual review cost", fmt(reviewCost)],
    ["Compliance risk cost", fmt(complianceRisk)],
    ["Audit cost", fmt(auditCost)],
    ["Total annual cost", fmt(totalWithout)],
  ];
  document.getElementById("withoutBreakdown").innerHTML = withoutItems.map(([l, v]) =>
    `<div class="row-item"><span class="label">${l}</span><span class="value">${v}</span></div>`
  ).join("");

  const withItems = [
    ["Annual incidents", dIncidents.toFixed(1)],
    ["Incident direct cost", fmt(dIncidentCost)],
    ["Incident value loss", fmt(dIncidentLoss)],
    ["Automated review cost", fmt(dReviewCost)],
    ["Residual compliance risk", fmt(dComplianceRisk)],
    ["Audit & replay cost", fmt(dAuditCost)],
    ["DSECS license", fmt(dLicense)],
    ["Total annual cost", fmt(totalWith)],
  ];
  document.getElementById("withBreakdown").innerHTML = withItems.map(([l, v]) =>
    `<div class="row-item"><span class="label">${l}</span><span class="value">${v}</span></div>`
  ).join("");

  document.getElementById("results").style.display = "block";
}
</script>
</body>
</html>
'''
    import os; path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../sales-kit/roi-calculator.html")
    path = os.path.normpath(path)
    with open(path, "w") as f:
        f.write(html)
    print(f"✅ Web calculator: {path}")


if __name__ == "__main__":
    main()
