import json
import csv
from pathlib import Path
from collections import defaultdict

def analyze_results():
    # 1. Map task_id to scope_type and calculate Breadth (number of files)
    task_info = {}
    tasks_dir = Path("tasks")
    for f in list(tasks_dir.glob("*.json")) + list((tasks_dir / "advanced").glob("*.json")):
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
    latest_csv = sorted(csv_files)[-1]
    
    results = []
    with open(latest_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            info = task_info.get(row["task_id"], {"scope_type": "unknown", "breadth": 0, "excess_potential": 0})
            row["scope_type"] = info["scope_type"]
            row["breadth"] = info["breadth"]
            row["excess_potential"] = info["excess_potential"]
            
            # Numeric conversion
            for key in ["refined_orr", "refined_eac", "tool_adjusted_pfa", "discovery_count", "true_overreach_count"]:
                row[key] = float(row[key])
            
            # New Metric: Reconnaissance Density (Discovery calls per run)
            # discovery_count is total list/read calls that weren't the final action
            row["recon_density"] = row["discovery_count"]
            
            # New Metric: Gap Closure Efficiency (GCE)
            # How many of the "extra" files did we NOT touch?
            # true_overreach_count is number of files/tools that were excess
            if row["excess_potential"] > 0:
                # Assuming overreach count relates to files
                row["gce"] = 1.0 - (row["true_overreach_count"] / row["excess_potential"])
                row["gce"] = max(0.0, row["gce"])
            else:
                row["gce"] = 1.0
                
            results.append(row)

    # --- New Insight 1: Permission Breadth vs ORR ---
    print("\n--- Insight: Permission Breadth Impact ---")
    breadth_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            group = "Narrow (<=5 files)" if r["breadth"] <= 5 else "Broad (>5 files)"
            breadth_groups[group].append(r["refined_orr"] * 100)
    
    for g, vals in sorted(breadth_groups.items()):
        print(f"{g:<20} => Avg ORR: {sum(vals)/len(vals):.1f}%")

    # --- New Insight 2: Reconnaissance Density ---
    print("\n--- Insight: Reconnaissance Density (Discovery Footprint) ---")
    recon_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            recon_groups[r["prompt_mode"]].append(r["recon_density"])
    
    for m, vals in sorted(recon_groups.items()):
        print(f"{m:<25} => Mean Discovery Calls: {sum(vals)/len(vals):.2f}")

    # --- New Insight 3: Gap Closure Efficiency (GCE) ---
    print("\n--- Insight: Gap Closure Efficiency (GCE) ---")
    gce_groups = defaultdict(list)
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            gce_groups[r["model"]].append(r["gce"] * 100)
            
    for m, vals in sorted(gce_groups.items()):
        print(f"{m:<40} => Mean GCE: {sum(vals)/len(vals):.1f}%")

    # Figure 1: Over-Reach Rate for Instruction Condition and Task Scope
    # Instruction Condition: baseline vs explicit_least_privilege
    fig1_data = defaultdict(lambda: {"total": 0, "count": 0})
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            key = (r["prompt_mode"], r["scope_type"])
            fig1_data[key]["total"] += r["refined_orr"]
            fig1_data[key]["count"] += 1
    
    print("\n--- Figure 1 Data: Over-Reach Rate (%) ---")
    for (pm, st), d in sorted(fig1_data.items()):
        avg = (d["total"] / d["count"]) * 100
        print(f"Condition: {pm}, Scope: {st} => {avg:.1f}%")

    # Figure 2: Over-Reach Rate by Model
    fig2_data = defaultdict(lambda: {"total": 0, "count": 0})
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            key = (r["model"], r["prompt_mode"])
            fig2_data[key]["total"] += r["refined_orr"]
            fig2_data[key]["count"] += 1
    
    print("\n--- Figure 2 Data: ORR by Model ---")
    for (m, pm), d in sorted(fig2_data.items()):
        avg = (d["total"] / d["count"]) * 100
        print(f"Model: {m}, Condition: {pm} => {avg:.1f}%")

    # Figure 3: Excess Access Count by Task Scope and Condition
    fig3_data = defaultdict(lambda: {"total": 0, "count": 0})
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            key = (r["scope_type"], r["prompt_mode"])
            fig3_data[key]["total"] += r["refined_eac"]
            fig3_data[key]["count"] += 1
            
    print("\n--- Figure 3 Data: Mean EAC ---")
    for (st, pm), d in sorted(fig3_data.items()):
        avg = d["total"] / d["count"]
        print(f"Scope: {st}, Condition: {pm} => {avg:.2f}")

    # Figure 4: Permission Floor Adherence by Model
    fig4_data = defaultdict(lambda: {"total": 0, "count": 0})
    for r in results:
        key = r["model"]
        fig4_data[key]["total"] += r["tool_adjusted_pfa"]
        fig4_data[key]["count"] += 1
        
    print("\n--- Figure 4 Data: PFA Adherence ---")
    for m, d in sorted(fig4_data.items()):
        avg = (d["total"] / d["count"]) * 100
        print(f"Model: {m} => {avg:.1f}%")

    # Table 1: Full Metric Summary
    table1_data = defaultdict(lambda: {"orr": [], "eac": [], "pfa": []})
    for r in results:
        if r["prompt_mode"] in ["baseline", "explicit_least_privilege"]:
            key = (r["model"], r["prompt_mode"], r["scope_type"])
            table1_data[key]["orr"].append(r["refined_orr"])
            table1_data[key]["eac"].append(r["refined_eac"])
            table1_data[key]["pfa"].append(r["tool_adjusted_pfa"])
            
    print("\n--- Table 1: Full Metric Summary ---")
    print(f"{'Model':<40} | {'Mode':<25} | {'Scope':<12} | {'ORR':<6} | {'EAC':<6} | {'PFA':<6}")
    for (m, pm, st), d in sorted(table1_data.items()):
        avg_orr = sum(d["orr"]) / len(d["orr"]) * 100
        avg_eac = sum(d["eac"]) / len(d["eac"])
        avg_pfa = sum(d["pfa"]) / len(d["pfa"]) * 100
        print(f"{m[:40]:<40} | {pm:<25} | {st:<12} | {avg_orr:4.1f}% | {avg_eac:4.2f} | {avg_pfa:4.1f}%")

if __name__ == "__main__":
    analyze_results()
