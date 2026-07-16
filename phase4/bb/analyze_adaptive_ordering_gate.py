from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent


def metric(record: dict, name: str) -> bool:
    return bool(record.get("logical_success", record.get("converged", False)))


def summarize(rows: list[dict]) -> dict:
    result = {}
    methods = ["baseline", "restart4", "beam4"]
    for method in methods:
        records = [row[method] for row in rows]
        result[method] = {
            "successes": sum(metric(record, method) for record in records),
            "mean_cost": float(np.mean([record.get("operation_ratio", record.get("operation_ratio_vs_serial_budget", record.get("total_decimations", record.get("decimations", 0)) / 1.0)) for record in records])) if records else 0.0,
        }
    for budget in (2, 3, 4):
        records = [row["adaptive"][str(budget)] for row in rows]
        result[f"adaptive_{budget}"] = {
            "successes": sum(metric(record, "adaptive") for record in records),
            "mean_cost": float(np.mean([record["operation_ratio"] for record in records])) if records else 0.0,
            "mean_reorders": float(np.mean([record["reorder_count"] for record in records])) if records else 0.0,
            "mean_probes": float(np.mean([record["probe_count"] for record in records])) if records else 0.0,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("curated", "train", "validation", "test"), default="curated")
    args = parser.parse_args()
    payload = json.loads((ROOT / f"adaptive_ordering_{args.split}_results.json").read_text(encoding="utf-8"))
    rows = payload["rows"]
    summary = summarize(rows)

    baseline_success = summary["baseline"]["successes"]
    restart_success = summary["restart4"]["successes"]
    candidates = []
    for budget in (2, 3, 4):
        item = summary[f"adaptive_{budget}"]
        candidates.append((item["successes"], -item["mean_cost"], budget))
    candidates.sort(reverse=True)
    _, _, best_budget = candidates[0]
    best = summary[f"adaptive_{best_budget}"]

    held_out = args.split in ("validation", "test")
    beats_baseline = best["successes"] > baseline_success
    matches_restart = best["successes"] >= restart_success
    cost_ok = best["mean_cost"] <= 1.5
    go = bool(held_out and beats_baseline and matches_restart and cost_ok)

    paired = {
        "adaptive_only_vs_baseline": [],
        "baseline_only_vs_adaptive": [],
        "adaptive_only_vs_restart": [],
        "restart_only_vs_adaptive": [],
    }
    for row in rows:
        adaptive = row["adaptive"][str(best_budget)]
        a = metric(adaptive, "adaptive")
        b = metric(row["baseline"], "baseline")
        r = metric(row["restart4"], "restart")
        if a and not b:
            paired["adaptive_only_vs_baseline"].append(row["case_id"])
        if b and not a:
            paired["baseline_only_vs_adaptive"].append(row["case_id"])
        if a and not r:
            paired["adaptive_only_vs_restart"].append(row["case_id"])
        if r and not a:
            paired["restart_only_vs_adaptive"].append(row["case_id"])

    decision = {
        "split": args.split,
        "best_budget": best_budget,
        "summary": summary,
        "paired": paired,
        "criteria": {
            "held_out_split": held_out,
            "beats_fixed_serial": beats_baseline,
            "matches_or_beats_restart4": matches_restart,
            "mean_cost_le_1_5": cost_ok,
        },
        "decision": "GO" if go else ("PROMISING_BUT_NOT_HELD_OUT" if (not held_out and beats_baseline and cost_ok) else "NO_GO_OR_REDESIGN"),
        "interpretation": "A GO requires a held-out logical-success gain over fixed serial, parity with restart-4, and <=1.5x mean operation cost.",
    }
    (ROOT / f"adaptive_ordering_{args.split}_analysis.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Adaptive Ordering Gate — {args.split}",
        "",
        f"**Decision: {decision['decision']}**",
        "",
        f"Best candidate budget: **{best_budget}**",
        "",
        "| Method | Successes | Mean cost ratio |",
        "|---|---:|---:|",
    ]
    for name, item in summary.items():
        lines.append(f"| {name} | {item['successes']} | {item['mean_cost']:.3f} |")
    lines += [
        "",
        "## Gate criteria",
        "",
        f"- Held-out split: {held_out}",
        f"- Beats fixed serial: {beats_baseline}",
        f"- Matches or beats restart-4: {matches_restart}",
        f"- Mean cost <= 1.5x: {cost_ok}",
        "",
        "## Boundary",
        "",
        "Curated results are mechanistic only. A scientific GO requires validation/test logical outcomes from the expanded corpus.",
    ]
    (ROOT / f"ADAPTIVE_ORDERING_{args.split.upper()}_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
