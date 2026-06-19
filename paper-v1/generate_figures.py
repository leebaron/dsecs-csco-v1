#!/usr/bin/env python3
"""DSECS Paper v1.0 — Figure Generator

Generates PNG figures for NeurIPS submission.
"""

import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FIGS_DIR = os.path.join(os.path.dirname(__file__), 'figures')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(FIGS_DIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'legend.fontsize': 10,
    'figure.dpi': 150,
})

COLORS = ['#00d4ff', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444']

def fig1_convergence():
    """Fig 1: GSAI convergence at different Byzantine ratios."""
    with open(os.path.join(DATA_DIR, 'convergence.json')) as f:
        data = json.load(f)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (ratio, vals) in enumerate(sorted(data.items())):
        trace = vals['gsai_trace'][:200]
        ax.plot(trace, label=f'Byzantine={float(ratio):.2f}', color=COLORS[i % len(COLORS)], linewidth=1.5)
    
    ax.set_xlabel('Time Step')
    ax.set_ylabel('GSAI Utility Score')
    ax.set_title('Figure 1: GSAI Convergence Under Varying Byzantine Ratios')
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = os.path.join(FIGS_DIR, 'fig1_convergence.png')
    fig.savefig(path)
    print(f"  ✅ {path}")
    plt.close(fig)

def fig2_byzantine_stress():
    """Fig 2: Byzantine survival rate."""
    with open(os.path.join(DATA_DIR, 'byzantine_stress.json')) as f:
        data = json.load(f)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    ratios = sorted([float(r) for r in data.keys()])
    success = [data[str(r)]['success_rate'] for r in ratios]
    mean_gsai = [data[str(r)]['mean_final_gsai'] for r in ratios]
    
    ax1.bar([str(r) for r in ratios], success, color=COLORS[2], alpha=0.8, width=0.6)
    ax1.set_xlabel('Byzantine Ratio')
    ax1.set_ylabel('Survival Rate')
    ax1.set_title('Figure 2a: Byzantine Attack Survival')
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3, axis='y')
    
    ax2.plot(ratios, mean_gsai, 'o-', color=COLORS[0], linewidth=2, markersize=8)
    ax2.fill_between(ratios, 
                     [data[str(r)]['min_final_gsai'] for r in ratios],
                     [data[str(r)]['max_final_gsai'] for r in ratios],
                     alpha=0.2, color=COLORS[0])
    ax2.set_xlabel('Byzantine Ratio')
    ax2.set_ylabel('Mean Final GSAI')
    ax2.set_title('Figure 2b: GSAI Under Attack')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(FIGS_DIR, 'fig2_byzantine_stress.png')
    fig.savefig(path)
    print(f"  ✅ {path}")
    plt.close(fig)

def fig3_ledger_integrity():
    """Fig 3: Ledger consistency verification."""
    with open(os.path.join(DATA_DIR, 'consistency.json')) as f:
        data = json.load(f)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    match = 1 if data['all_nodes_match'] else 0
    mismatch = 0 if data['all_nodes_match'] else 1
    bars = ax.bar(['Genesis Prefix Match'], [match * 100], color=COLORS[2], alpha=0.8, width=0.5)
    ax.text(bars[0].get_x() + bars[0].get_width()/2., bars[0].get_height()/2.,
            f'{int(match*100)}%', ha='center', va='center', fontsize=16, fontweight='bold', color='white')
    ax.set_ylabel('Nodes with Matching Genesis (%)')
    ax.set_title('Figure 3: Ledger Genesis Consistency\n(10 independent nodes, genesis(42))')
    ax.set_ylim(0, 120)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    path = os.path.join(FIGS_DIR, 'fig3_ledger_integrity.png')
    fig.savefig(path)
    print(f"  ✅ {path}")
    plt.close(fig)

def fig4_ablation():
    """Fig 4: Ablation study."""
    with open(os.path.join(DATA_DIR, 'ablation.json')) as f:
        data = json.load(f)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Final GSAI bar chart
    labels = list(data.keys())
    final_gsai = [data[k]['final_gsai'] for k in labels]
    colors = [COLORS[2] if k == 'full' else COLORS[4] if k == 'no_csco' else COLORS[3] for k in labels]
    
    bars = ax1.bar(labels, final_gsai, color=colors, alpha=0.8, width=0.6)
    ax1.set_xlabel('Configuration')
    ax1.set_ylabel('Final GSAI Score')
    ax1.set_title('Figure 4a: Ablation — Final GSAI')
    ax1.set_xticklabels(labels, rotation=15)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add values on bars
    i_diverges = labels.index('no_csco')
    if data['no_csco']['final_gsai'] > 5:
        for i, bar in enumerate(bars):
            val = final_gsai[i]
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                    f'{val:.2f}', ha='center', fontsize=8)
        ax1.set_ylim(0, max(final_gsai) * 1.15)
    
    # Trace comparison
    for i, k in enumerate(labels):
        trace = data[k].get('gsai_trace', [])
        if not trace:
            trace = [data[k].get('final_gsai', 0)]
        ax2.plot(trace[:100], label=k, color=list(colors)[i] if i < len(colors) else None,
                linewidth=1.5, alpha=0.8)
    ax2.set_xlabel('Time Step')
    ax2.set_ylabel('GSAI Score')
    ax2.set_title('Figure 4b: Ablation — Early Dynamics')
    ax2.legend(frameon=False, fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(FIGS_DIR, 'fig4_ablation.png')
    fig.savefig(path)
    print(f"  ✅ {path}")
    plt.close(fig)

def main():
    print("═══ DSECS Paper v1.0 — Figure Generator ═══\n")
    fig1_convergence()
    fig2_byzantine_stress()
    fig3_ledger_integrity()
    fig4_ablation()
    print(f"\nAll figures saved to {FIGS_DIR}/")
    for f in sorted(os.listdir(FIGS_DIR)):
        if f.endswith('.png'):
            size = os.path.getsize(os.path.join(FIGS_DIR, f))
            print(f"  {f:30s} {size/1024:.1f} KB")

if __name__ == '__main__':
    main()
