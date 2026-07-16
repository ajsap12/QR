from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent


def first_decision_divergence(serial: list[dict], parallel: list[dict]) -> int | None:
    limit = min(len(serial), len(parallel))
    for index in range(limit):
        a = serial[index]
        b = parallel[index]
        if (
            a.get("selected_variable") != b.get("selected_variable")
            or a.get("selected_hard_bit") != b.get("selected_hard_bit")
        ):
            return index
    return limit if len(serial) != len(parallel) else None


def classify(serial: dict, parallel: dict, divergence: int | None) -> str:
    s_traj = serial["trajectory"]
    p_traj = parallel["trajectory"]
    if serial["converged"] and not parallel["converged"]:
        if divergence is not None and divergence <= 5:
            return "early_decision_divergence"
        p_residual = [step["residual_syndrome_weight"] for step in p_traj]
        p_changes = [step["changed_hard_decisions"] for step in p_traj]
        if len(p_residual) >= 4 and len(set(p_residual[-4:])) == 1:
            return "parallel_residual_stall"
        if sum(value > 0 for value in p_changes[-6:]) >= 4:
            return "parallel_hard_decision_oscillation"
        s_gaps = [step.get("reliability_gap") for step in s_traj if step.get("reliability_gap") is not None]
        p_gaps = [step.get("reliability_gap") for step in p_traj if step.get("reliability_gap") is not None]
        if s_gaps and p_gaps and float(np.median(s_gaps)) > float(np.median(p_gaps)):
            return "serial_reliability_separation"
        return "serial_only_success_unclassified"
    if not serial["converged"] and not parallel["converged"]:
        return "shared_invariant_failure"
    if parallel["converged"] and not serial["converged"]:
        return "parallel_only_success"
    return "both_converge"


def summarize_path(trajectory: list[dict]) -> dict:
    residuals = [int(step["residual_syndrome_weight"]) for step in trajectory]
    gaps = [float(step["reliability_gap"]) for step in trajectory if step.get("reliability_gap") is not None]
    changes = [int(step["changed_hard_decisions"]) for step in trajectory]
    selected = [step.get("selected_variable") for step in trajectory if step.get("selected_variable") is not None]
    non_improving = sum(
        1 for index in range(1, len(residuals)) if residuals[index] >= residuals[index - 1]
    )
    return {
        "rounds": len(trajectory),
        "initial_residual": residuals[0] if residuals else None,
        "minimum_residual": min(residuals) if residuals else None,
        "final_residual": residuals[-1] if residuals else None,
        "non_improving_steps": non_improving,
        "mean_changed_hard_decisions": float(np.mean(changes)) if changes else 0.0,
        "median_reliability_gap": float(np.median(gaps)) if gaps else None,
        "selected_variables": selected,
    }


def main() -> None:
    payload = json.loads((ROOT / "schedule_trajectory_results.json").read_text(encoding="utf-8"))
    cases = []
    categories = Counter()
    serial_only_cases = []

    for case in payload["cases"]:
        serial = case["schedules"]["serial"]
        parallel = case["schedules"]["parallel"]
        divergence = first_decision_divergence(serial["trajectory"], parallel["trajectory"])
        category = classify(serial, parallel, divergence)
        categories[category] += 1
        record = {
            "syndrome_sha256": case["syndrome_sha256"],
            "code": case["code"],
            "sector": case["sector"],
            "syndrome_weight": case["syndrome_weight"],
            "serial_converged": serial["converged"],
            "parallel_converged": parallel["converged"],
            "first_decision_divergence_round": divergence,
            "classification": category,
            "serial": summarize_path(serial["trajectory"]),
            "parallel": summarize_path(parallel["trajectory"]),
        }
        cases.append(record)
        if serial["converged"] and not parallel["converged"]:
            serial_only_cases.append(record)

    divergence_rounds = [
        item["first_decision_divergence_round"]
        for item in serial_only_cases
        if item["first_decision_divergence_round"] is not None
    ]
    analysis = {
        "experiment": "serial_parallel_mechanism_analysis_v1",
        "input_case_count": payload["input_case_count"],
        "serial_successes": sum(item["serial_converged"] for item in cases),
        "parallel_successes": sum(item["parallel_converged"] for item in cases),
        "serial_only_successes": len(serial_only_cases),
        "classification_counts": dict(categories),
        "serial_only_median_divergence_round": float(np.median(divergence_rounds)) if divergence_rounds else None,
        "serial_only_cases": serial_only_cases,
        "cases": cases,
        "scientific_gate": {
            "mechanism_signal_present": bool(serial_only_cases),
            "candidate_generalization": "adaptive update ordering or state-dependent layered scheduling",
            "required_next_test": "Validate serial-vs-parallel logical success and operation cost on a held-out randomized corpus.",
        },
        "boundary": payload["boundary"],
    }
    (ROOT / "schedule_trajectory_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Serial vs Parallel BPGD Trajectory Analysis",
        "",
        f'- Curated cases: **{analysis["input_case_count"]}**',
        f'- Serial successes: **{analysis["serial_successes"]}**',
        f'- Parallel successes: **{analysis["parallel_successes"]}**',
        f'- Serial-only successes: **{analysis["serial_only_successes"]}**',
        f'- Median first divergence round on serial-only cases: **{analysis["serial_only_median_divergence_round"]}**',
        "",
        "## Failure mechanism classes",
        "",
        "| Class | Cases |",
        "|---|---:|",
    ]
    for category, count in sorted(categories.items()):
        lines.append(f"| {category} | {count} |")
    lines += [
        "",
        "## Serial-only cases",
        "",
        "| Syndrome | Code | Sector | Divergence round | Class | Serial min residual | Parallel min residual |",
        "|---|---|---|---:|---|---:|---:|",
    ]
    for item in serial_only_cases:
        lines.append(
            f'| `{item["syndrome_sha256"][:12]}` | {item["code"]} | {item["sector"]} | '
            f'{item["first_decision_divergence_round"]} | {item["classification"]} | '
            f'{item["serial"]["minimum_residual"]} | {item["parallel"]["minimum_residual"]} |'
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This analysis does not claim that serial BPGD is state of the art. It tests whether its advantage on the curated failure corpus is associated with a reproducible trajectory mechanism that could motivate a new adaptive scheduler.",
        "",
        analysis["boundary"],
    ]
    (ROOT / "SCHEDULE_TRAJECTORY_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "serial_successes": analysis["serial_successes"],
        "parallel_successes": analysis["parallel_successes"],
        "classification_counts": analysis["classification_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
