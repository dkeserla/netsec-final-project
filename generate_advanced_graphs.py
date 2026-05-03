import json
import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

def generate_scientific_visualizations():
    # 1. Load Data
    metrics_path = Path("analysis/all_tasks_metrics.json")
    if not metrics_path.exists():
        print("Data not found")
        return
    with open(metrics_path, "r") as f:
        results = json.load(f)
        # Ensure numeric fields are floats
        for r in results:
            for key in ["discovery_count", "refined_orr", "gce", "tool_adjusted_pfa", "breadth"]:
                if key in r and r[key] is not None:
                    r[key] = float(r[key])

    # Helper for grouping
    def get_avg(data_list):
        return sum(data_list) / len(data_list) if data_list else 0

    modes = ["baseline", "explicit_least_privilege"]
    models = sorted(list(set(r["model"] for r in results)))
    model_labels = [m.split('/')[-1] for m in models]

    # Set global plotting style
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 12,
        'figure.titlesize': 18
    })

    # --- FIGURE 8: THE VERIFICATION TAX (Stacked Discovery vs. Action) ---
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    
    discovery_baseline = []
    discovery_lp = []
    
    for m in models:
        b_vals = [r["discovery_count"] for r in results if r["model"] == m and r["prompt_mode"] == "baseline"]
        discovery_baseline.append(get_avg(b_vals))
        lp_vals = [r["discovery_count"] for r in results if r["model"] == m and r["prompt_mode"] == "explicit_least_privilege"]
        discovery_lp.append(get_avg(lp_vals))

    x = np.arange(len(model_labels))
    width = 0.35
    
    b1 = ax.bar(x - width/2, discovery_baseline, width, label='Baseline Discovery', color='#aec7e8', edgecolor='black', linewidth=0.8, alpha=0.9)
    b2 = ax.bar(x + width/2, discovery_lp, width, label='Explicit LP Discovery', color='#1f77b4', edgecolor='black', linewidth=0.8, alpha=0.9)
    
    # Add value labels
    for bars in [b1, b2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.05, f'{height:.2f}', ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Mean Discovery Calls (System Footprint)', fontweight='bold')
    ax.set_title('Figure 8: The Verification Tax\n(Instruction-Induced Discovery Growth)', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, rotation=15, fontweight='bold')
    ax.set_ylim(0, max(discovery_baseline + discovery_lp + [1.0]) * 1.3)
    ax.legend(frameon=True, shadow=True)
    plt.tight_layout()
    plt.savefig('figures/figure8_verification_tax.png', bbox_inches='tight')
    plt.close()

    # --- FIGURE 9: THE SURGICAL TRIGGER PARADOX (Binned Analysis) ---
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    
    # Define bins
    bins = ["Narrow (≤5 Files)", "Broad (>5 Files)"]
    scopes = ["well_scoped", "ambiguous"]
    
    # Prepare data
    binned_data = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            b_bin = bins[0] if r["breadth"] <= 5 else bins[1]
            binned_data[(b_bin, r["scope_type"])].append(r["refined_orr"] * 100)
    
    x = np.arange(len(bins))
    width = 0.35
    
    # Plot bars
    well_vals = [get_avg(binned_data[(b, "well_scoped")]) for b in bins]
    ambig_vals = [get_avg(binned_data[(b, "ambiguous")]) for b in bins]
    
    b1 = ax.bar(x - width/2, well_vals, width, label='Well-Scoped Tasks', color='#2ca02c', alpha=0.85, edgecolor='black', linewidth=0.8)
    b2 = ax.bar(x + width/2, ambig_vals, width, label='Ambiguous Tasks', color='#d62728', alpha=0.85, edgecolor='black', linewidth=0.8)
    
    # Add value labels
    for bars in [b1, b2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{height:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Mean Over-Reach Rate (%)', fontweight='bold')
    ax.set_title('Figure 9: The Surgical Trigger Paradox\n(Over-Reach decreases as Workspace Breadth increases for Ambiguous tasks)', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(bins, fontweight='bold')
    ax.set_ylim(0, max(well_vals + ambig_vals + [15]) * 1.3)
    ax.legend(frameon=True, shadow=True, title="Task Clarity")
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('figures/figure9_surgical_trigger.png', bbox_inches='tight')
    plt.close()

    # --- FIGURE 10: MODEL SECURITY FINGERPRINTS (Polar/Radar Approximation) ---
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    
    metric_labels = ['Gap Closure Efficiency', 'Permission Adherence', 'Operating Precision (100-ORR)']
    
    for i, m in enumerate(models):
        m_results = [r for r in results if r["model"] == m and r["prompt_mode"] == "explicit_least_privilege"]
        gce = get_avg([r["gce"] for r in m_results]) * 100
        pfa = get_avg([r["tool_adjusted_pfa"] for r in m_results]) * 100
        prec = 100 - (get_avg([r["refined_orr"] for r in m_results]) * 100)
        
        vals = [gce, pfa, prec]
        bars = ax.bar(np.arange(3) + (i - (len(models)-1)/2)*0.2, vals, 0.2, label=model_labels[i], alpha=0.85, edgecolor='black', linewidth=0.8)
        # Only label the best performing to avoid clutter, or all if it looks okay
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.0f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('Score (%)', fontweight='bold')
    ax.set_title('Figure 10: Model Security Fingerprints\n(Comparative Multi-Metric Alignment)', pad=20)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(metric_labels, fontweight='bold')
    ax.set_ylim(0, 118)
    ax.legend(loc='upper right', frameon=True, shadow=True, ncol=2)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('figures/figure10_fingerprints.png', bbox_inches='tight')
    plt.close()

    print("Scientific-grade visualizations (8-10) generated.")

if __name__ == "__main__":
    generate_scientific_visualizations()
