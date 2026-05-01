import json
import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

def generate_visualizations():
    # 1. Map task_id to scope_type and calculate Breadth
    task_info = {}
    tasks_dir = Path("tasks")
    all_task_files = list(tasks_dir.glob("*.json"))
    advanced_dir = tasks_dir / "advanced"
    if advanced_dir.exists():
        all_task_files += list(advanced_dir.glob("*.json"))

    for f in all_task_files:
        with open(f, "r") as jf:
            data = json.load(jf)
            tid = data["task_id"]
            num_files = len(data["workspace"]["files"])
            required_files = len(data["gold_min_access_set"].get("file_access", {}))
            
            task_info[tid] = {
                "scope_type": data.get("scope_type", "well_scoped") if "advanced" not in str(f) else "ambiguous",
                "breadth": num_files,
                "excess_potential": num_files - required_files,
                "required_files": required_files
            }

    # 2. Parse CSV
    aggregates_dir = Path("outputs_all_tasks/aggregates")
    csv_files = list(aggregates_dir.glob("*_results.csv"))
    if not csv_files:
        print("No CSV found")
        return
    
    latest_csv = sorted(csv_files)[-1]
    results = []
    with open(latest_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Merge Metadata
            info = task_info.get(row["task_id"], {"scope_type": "unknown", "breadth": 0, "excess_potential": 0})
            row.update(info)
            
            for key in ["refined_orr", "refined_eac", "tool_adjusted_pfa", "discovery_count", "true_overreach_count"]:
                row[key] = float(row[key])
            
            row["recon_density"] = row["discovery_count"]
            if row["excess_potential"] > 0:
                row["gce"] = 1.0 - (row["true_overreach_count"] / row["excess_potential"])
                row["gce"] = max(0.0, row["gce"])
            else:
                row["gce"] = 1.0
                
            results.append(row)

    # Store metrics (CRITICAL: make sure all fields are here)
    metrics_path = Path("analysis/all_tasks_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Stored raw results in {metrics_path}")

    # Helper for grouping
    def get_avg(data_list):
        return sum(data_list) / len(data_list) if data_list else 0

    modes = ["baseline", "explicit_least_privilege"]
    scopes = ["well_scoped", "ambiguous"]
    models = sorted(list(set(r["model"] for r in results)))
    model_labels = [m.split('/')[-1] for m in models]
    width = 0.35

    # Figure 1: ORR by Instruction Condition and Task Scope
    fig1_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            fig1_groups[(r["prompt_mode"], r["scope_type"])].append(r["refined_orr"] * 100)
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(modes))
    for i, scope in enumerate(scopes):
        vals = [get_avg(fig1_groups[(m, scope)]) for m in modes]
        ax.bar(x + (i - 0.5) * width, vals, width, label=scope)
    ax.set_ylabel('Over-Reach Rate (%)')
    ax.set_title('Figure 1: ORR by Instruction Condition and Task Scope')
    ax.set_xticks(x)
    ax.set_xticklabels(["No Instruction", "Explicit LP"])
    ax.legend()
    plt.savefig('analysis/figure1_orr_scope.png')
    plt.close()

    # Figure 2: ORR by Model
    fig2_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            fig2_groups[(r["model"], r["prompt_mode"])].append(r["refined_orr"] * 100)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(models))
    for i, mode in enumerate(modes):
        vals = [get_avg(fig2_groups[(m, mode)]) for m in models]
        ax.bar(x + (i - 0.5) * width, vals, width, label=mode)
    ax.set_ylabel('Over-Reach Rate (%)')
    ax.set_title('Figure 2: Over-Reach Rate by Model')
    ax.set_xticks(x)
    ax.set_xticklabels([m.split('/')[-1] for m in models], rotation=15)
    ax.legend()
    plt.tight_layout()
    plt.savefig('analysis/figure2_orr_model.png')
    plt.close()

    # Figure 3: Mean EAC by Scope and Condition
    fig3_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            fig3_groups[(r["scope_type"], r["prompt_mode"])].append(r["refined_eac"])
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(scopes))
    for i, mode in enumerate(modes):
        vals = [get_avg(fig3_groups[(s, mode)]) for s in scopes]
        ax.bar(x + (i - 0.5) * width, vals, width, label=mode)
    ax.set_ylabel('Mean Excess Access Count')
    ax.set_title('Figure 3: Excess Access Count by Scope and Condition')
    ax.set_xticks(x)
    ax.set_xticklabels(scopes)
    ax.legend()
    plt.savefig('analysis/figure3_eac.png')
    plt.close()

    # Figure 4: PFA by Model
    fig4_groups = defaultdict(list)
    for r in results:
        fig4_groups[r["model"]].append(r["tool_adjusted_pfa"] * 100)
    fig, ax = plt.subplots(figsize=(10, 6))
    vals = [get_avg(fig4_groups[m]) for m in models]
    ax.bar([m.split('/')[-1] for m in models], vals, color='green')
    ax.set_ylabel('PFA Adherence (%)')
    ax.set_title('Figure 4: Permission Floor Adherence by Model')
    ax.set_ylim(0, 110)
    plt.savefig('analysis/figure4_pfa.png')
    plt.close()

    # Advanced Figures (5-7)
    # Figure 5: GCE
    fig5_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            fig5_groups[r["model"]].append(r["gce"] * 100)
    fig, ax = plt.subplots(figsize=(10, 6))
    vals = [get_avg(fig5_groups[m]) for m in models]
    ax.bar(model_labels, vals, color='purple')
    ax.set_ylabel('Mean GCE (%)')
    ax.set_title('Figure 5: Gap Closure Efficiency by Model')
    ax.set_ylim(0, 110)
    plt.savefig('analysis/figure5_gce.png')
    plt.close()

    # Figure 6: Recon
    fig6_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            fig6_groups[r["prompt_mode"]].append(r["recon_density"])
    fig, ax = plt.subplots(figsize=(10, 6))
    vals = [get_avg(fig6_groups[m]) for m in modes]
    ax.bar(["No Instruction", "Explicit LP"], vals, color='orange')
    ax.set_ylabel('Mean Discovery Calls')
    ax.set_title('Figure 6: Reconnaissance Density by Condition')
    plt.savefig('analysis/figure6_recon.png')
    plt.close()

    # Figure 7: Breadth
    fig7_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in modes:
            group = "Narrow (<=5)" if r["breadth"] <= 5 else "Broad (>5)"
            fig7_groups[group].append(r["refined_orr"] * 100)
    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_groups = sorted(fig7_groups.keys())
    vals = [get_avg(fig7_groups[g]) for g in sorted_groups]
    ax.bar(sorted_groups, vals, color='teal')
    ax.set_ylabel('Over-Reach Rate (%)')
    ax.set_title('Figure 7: ORR by Permission Breadth')
    plt.savefig('analysis/figure7_breadth.png')
    plt.close()

    print("All graphs (1-7) generated in analysis/")

if __name__ == "__main__":
    generate_visualizations()
