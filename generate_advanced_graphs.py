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

    # --- FIGURE 8: THE VERIFICATION TAX (Stacked Discovery vs. Action) ---
    # We want to show that Discovery calls increase with LP instructions
    fig, ax = plt.subplots(figsize=(10, 7))
    
    discovery_baseline = []
    discovery_lp = []
    
    for m in models:
        # Get mean discovery for this model in baseline
        b_vals = [r["discovery_count"] for r in results if r["model"] == m and r["prompt_mode"] == "baseline"]
        discovery_baseline.append(get_avg(b_vals))
        
        # Get mean discovery for this model in explicit_lp
        lp_vals = [r["discovery_count"] for r in results if r["model"] == m and r["prompt_mode"] == "explicit_least_privilege"]
        discovery_lp.append(get_avg(lp_vals))

    x = np.arange(len(model_labels))
    width = 0.35
    
    ax.bar(x - width/2, discovery_baseline, width, label='Baseline Discovery', color='#aec7e8')
    ax.bar(x + width/2, discovery_lp, width, label='Explicit LP Discovery', color='#1f77b4')
    
    ax.set_ylabel('Mean Discovery Calls (System Footprint)')
    ax.set_title('Figure 8: The Verification Tax\n(Instruction-Induced Discovery Growth)')
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, rotation=15)
    ax.legend()
    plt.tight_layout()
    plt.savefig('analysis/figure8_verification_tax.png')
    plt.close()

    # --- FIGURE 9: THE SURGICAL TRIGGER (Workspace Size vs. ORR Trend) ---
    # Scatter plot: Breadth (X) vs ORR (Y)
    fig, ax = plt.subplots(figsize=(10, 7))
    
    x_breadth = [r["breadth"] for r in results if r["prompt_mode"] in modes]
    y_orr = [r["refined_orr"] * 100 for r in results if r["prompt_mode"] in modes]
    
    # Scatter with transparency to show density
    ax.scatter(x_breadth, y_orr, alpha=0.5, s=100, color='#d62728', edgecolors='black')
    
    # Add a trendline
    z = np.polyfit(x_breadth, y_orr, 1)
    p = np.poly1d(z)
    ax.plot(sorted(x_breadth), p(sorted(x_breadth)), "r--", alpha=0.8, label='Paradox Trend')

    ax.set_xlabel('Workspace Breadth (Total Authorized Files)')
    ax.set_ylabel('Over-Reach Rate (%)')
    ax.set_title('Figure 9: The Surgical Trigger Paradox\n(Agents become more precise as noise increases)')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    plt.savefig('analysis/figure9_surgical_trigger.png')
    plt.close()

    # --- FIGURE 10: MODEL SECURITY FINGERPRINTS (Polar/Radar Approximation) ---
    # Since Radar is complex in matplotlib, we'll use a grouped multi-metric bar chart
    # Metrics: GCE, PFA, (100 - ORR) for "Precision"
    fig, ax = plt.subplots(figsize=(12, 7))
    
    metric_labels = ['Gap Closure Efficiency', 'Permission Adherence', 'Operating Precision (100-ORR)']
    
    for i, m in enumerate(models):
        m_results = [r for r in results if r["model"] == m and r["prompt_mode"] == "explicit_least_privilege"]
        gce = get_avg([r["gce"] for r in m_results]) * 100
        pfa = get_avg([r["tool_adjusted_pfa"] for r in m_results]) * 100
        prec = 100 - (get_avg([r["refined_orr"] for r in m_results]) * 100)
        
        vals = [gce, pfa, prec]
        ax.bar(np.arange(3) + (i - 1)*0.25, vals, 0.25, label=model_labels[i])

    ax.set_ylabel('Score (%)')
    ax.set_title('Figure 10: Model Security Fingerprints\n(Comparative Multi-Metric Alignment)')
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(metric_labels)
    ax.set_ylim(0, 115)
    ax.legend(loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('analysis/figure10_fingerprints.png')
    plt.close()

    print("Scientific-grade visualizations (8-10) generated.")

if __name__ == "__main__":
    generate_scientific_visualizations()
