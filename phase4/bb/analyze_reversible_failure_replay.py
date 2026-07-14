from __future__ import annotations

import json
from pathlib import Path


INVARIANT_HASHES = {
    "83cc513e8352f861d464fc57dee727be48466bfc45929f6b528cfe5a79fef44a",
    "bcc41e95e64626fa10ec9313a47460542b4edbefd4e1c4f0a2fab42de9caac5a",
}


def main() -> None:
    root = Path(__file__).parent
    payload = json.loads((root / "reversible_bpgd_results.json").read_text(encoding="utf-8"))
    baseline = next(item for item in payload["summary"] if item["max_backtracks"] == 0)
    best = max(payload["summary"], key=lambda item: (item["resolved"], -item["mean_operation_ratio"]))

    invariant_rows = []
    for case in payload["cases"]:
        if case["syndrome_sha256"] not in INVARIANT_HASHES:
            continue
        invariant_rows.append({
            "syndrome_sha256": case["syndrome_sha256"],
            "results": [
                {
                    "depth": variant["max_backtracks"],
                    "converged": variant["converged"],
                    "residual": variant["residual_syndrome_weight"],
                    "backtracks": variant["backtracks_used"],
                    "operation_ratio": variant["operation_ratio_vs_serial_budget"],
                }
                for variant in case["variants"]
            ],
        })

    additional = best["resolved"] - baseline["resolved"]
    invariant_resolved = sum(
        any(item["converged"] for item in row["results"] if item["depth"] > 0)
        for row in invariant_rows
    )
    no_regressions = True
    for case in payload["cases"]:
        base = next(item for item in case["variants"] if item["max_backtracks"] == 0)
        candidate = next(
            item for item in case["variants"]
            if item["max_backtracks"] == best["max_backtracks"] and item["decoder"] == best["decoder"]
        )
        if base["converged"] and not candidate["converged"]:
            no_regressions = False
            break

    gate_pass = (
        (invariant_resolved == len(invariant_rows) or additional >= 2)
        and best["max_operation_ratio"] <= 2.0
        and no_regressions
    )

    analysis = {
        "gate": "RBGD Gate 1",
        "passed": gate_pass,
        "baseline_resolved": baseline["resolved"],
        "best_variant": best,
        "additional_cases_resolved": additional,
        "invariant_cases_resolved": invariant_resolved,
        "invariant_case_count": len(invariant_rows),
        "no_regressions_on_serial_successes": no_regressions,
        "criteria": {
            "accuracy": "Resolve both invariant cases or at least two additional cases beyond serial BPGD.",
            "cost": "Maximum operation ratio no greater than 2.0 versus the serial decimation budget.",
            "safety": "Do not regress any case already solved by serial BPGD.",
        },
        "invariant_cases": invariant_rows,
        "interpretation": (
            "PASS means bounded rollback warrants randomized validation; it does not establish a lower logical-error rate."
            if gate_pass
            else "FAIL means this rollback rule should be redesigned or stopped before randomized benchmarking."
        ),
    }
    (root / "reversible_bpgd_gate_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Reversible BPGD — Gate 1 Analysis",
        "",
        f"**Gate result:** {'PASS' if gate_pass else 'FAIL'}",
        "",
        f"- Serial BPGD resolved: **{baseline['resolved']}/{payload['input_case_count']}**",
        f"- Best bounded-rollback variant: depth **{best['max_backtracks']}**, resolved **{best['resolved']}/{payload['input_case_count']}**",
        f"- Additional cases resolved: **{additional}**",
        f"- Invariant cases resolved: **{invariant_resolved}/{len(invariant_rows)}**",
        f"- Maximum operation ratio: **{best['max_operation_ratio']:.3f}×**",
        f"- Regressions on serial successes: **{'none' if no_regressions else 'present'}**",
        "",
        "## Variant summary",
        "",
        "| Decoder | Backtrack depth | Resolved | Unresolved | Mean operation ratio | Max operation ratio |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in payload["summary"]:
        lines.append(
            f"| {item['decoder']} | {item['max_backtracks']} | {item['resolved']} | {item['unresolved']} | "
            f"{item['mean_operation_ratio']:.3f} | {item['max_operation_ratio']:.3f} |"
        )
    lines += ["", "## Invariant cases", ""]
    for row in invariant_rows:
        lines.append(f"### `{row['syndrome_sha256']}`")
        lines.append("")
        lines.append("| Depth | Converged | Residual | Backtracks | Operation ratio |")
        lines.append("|---:|---:|---:|---:|---:|")
        for item in row["results"]:
            lines.append(
                f"| {item['depth']} | {item['converged']} | {item['residual']} | {item['backtracks']} | {item['operation_ratio']:.3f} |"
            )
        lines.append("")
    lines += [
        "## Interpretation boundary",
        "",
        analysis["interpretation"],
        "",
        "The 17 cases are a selected failure corpus. A passing result must be followed by matched randomized tests on BB code families before any performance or novelty claim.",
    ]
    (root / "REVERSIBLE_BPGD_GATE_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
