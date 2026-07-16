from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent


def common_prefix(a: list[int], b: list[int]) -> int:
    limit = min(len(a), len(b))
    for index in range(limit):
        if a[index] != b[index]:
            return index
    return limit


def main() -> None:
    path = ROOT / "gate2_control_results.json"
    if not path.exists():
        raise FileNotFoundError("Run run_gate2_controls.py first")
    payload = json.loads(path.read_text(encoding="utf-8"))

    findings = []
    for case in payload["cases"]:
        restart4 = next(
            item for item in case["controls"]
            if item["decoder"] == "random_restart_bpgd" and item["attempt_budget"] == 4
        )
        restart1 = next(
            item for item in case["controls"]
            if item["decoder"] == "random_restart_bpgd" and item["attempt_budget"] == 1
        )
        if restart1["converged"] or not restart4["converged"]:
            continue

        baseline = restart4["runs"][0]
        successful = next(run for run in restart4["runs"] if run["converged"])
        prefix = common_prefix(baseline["selected_variables"], successful["selected_variables"])
        findings.append({
            "syndrome_sha256": case["syndrome_sha256"],
            "code": case["code"],
            "sector": case["sector"],
            "successful_seed": successful["seed"],
            "attempt_index": restart4["runs"].index(successful),
            "baseline_residual": baseline["residual_syndrome_weight"],
            "successful_residual": successful["residual_syndrome_weight"],
            "baseline_decimations": baseline["decimations"],
            "successful_decimations": successful["decimations"],
            "common_decision_prefix": prefix,
            "baseline_divergence_window": baseline["selected_variables"][prefix:prefix + 8],
            "successful_divergence_window": successful["selected_variables"][prefix:prefix + 8],
            "interpretation": (
                "The successful restart preserved a long common prefix and first differed by candidate order. "
                "This supports targeted path diversity as the next hypothesis, not wholesale restart or local rollback."
            ),
        })

    analysis = {
        "experiment": "restart_divergence_analysis_v1",
        "restart_only_success_count": len(findings),
        "cases": findings,
        "boundary": (
            "This analysis identifies trajectory divergence from selected-variable order only. "
            "A future instrumented run must also record per-step LLRs, selected bits, and residual trajectories."
        ),
    }
    (ROOT / "restart_divergence_analysis.json").write_text(
        json.dumps(analysis, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Random-Restart Divergence Analysis",
        "",
        f'- Restart-only successes: **{len(findings)}**',
        "",
    ]
    for finding in findings:
        lines += [
            f'## `{finding["syndrome_sha256"]}`',
            "",
            f'- Code/sector: **{finding["code"]} / {finding["sector"]}**',
            f'- Successful seed: **{finding["successful_seed"]}**',
            f'- Successful attempt index: **{finding["attempt_index"]}**',
            f'- Common decision prefix: **{finding["common_decision_prefix"]}**',
            f'- Baseline divergence window: `{finding["baseline_divergence_window"]}`',
            f'- Successful divergence window: `{finding["successful_divergence_window"]}`',
            f'- Baseline decimations/residual: **{finding["baseline_decimations"]} / {finding["baseline_residual"]}**',
            f'- Successful decimations/residual: **{finding["successful_decimations"]} / {finding["successful_residual"]}**',
            "",
            finding["interpretation"],
            "",
        ]
    lines += ["## Interpretation boundary", "", analysis["boundary"]]
    (ROOT / "RESTART_DIVERGENCE_ANALYSIS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
