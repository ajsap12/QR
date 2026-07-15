from __future__ import annotations

import json
from collections import Counter, deque
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel

ROOT = Path(__file__).parent


def connected_components(checks: np.ndarray, active_checks: np.ndarray) -> list[dict[str, object]]:
    active = set(map(int, np.flatnonzero(active_checks)))
    check_to_vars = {c: set(map(int, np.flatnonzero(checks[c]))) for c in active}
    var_to_checks: dict[int, set[int]] = {}
    for check, variables in check_to_vars.items():
        for variable in variables:
            var_to_checks.setdefault(variable, set()).add(check)

    components = []
    unseen = set(active)
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        component_checks = {start}
        component_vars: set[int] = set()
        while queue:
            check = queue.popleft()
            for variable in check_to_vars[check]:
                component_vars.add(variable)
                for neighbor in var_to_checks.get(variable, ()):
                    if neighbor not in component_checks:
                        component_checks.add(neighbor)
                        unseen.discard(neighbor)
                        queue.append(neighbor)
        components.append({
            "check_count": len(component_checks),
            "variable_count": len(component_vars),
            "checks": sorted(component_checks),
            "variables": sorted(component_vars),
        })
    return sorted(components, key=lambda item: (-item["check_count"], -item["variable_count"]))


def count_four_cycles(checks: np.ndarray, variables: list[int]) -> int:
    if len(variables) < 2:
        return 0
    sub = checks[:, variables]
    overlaps = sub.T @ sub
    count = 0
    for i in range(overlaps.shape[0]):
        for j in range(i + 1, overlaps.shape[1]):
            overlap = int(overlaps[i, j])
            if overlap >= 2:
                count += overlap * (overlap - 1) // 2
    return count


def trajectory_summary(trajectory: list[dict[str, object]]) -> dict[str, object]:
    residuals = [int(step["residual_syndrome_weight"]) for step in trajectory]
    gaps = [float(step.get("reliability_gap", 0.0)) for step in trajectory]
    return {
        "rounds": len(trajectory),
        "initial_residual": residuals[0] if residuals else None,
        "final_residual": residuals[-1] if residuals else None,
        "minimum_residual": min(residuals) if residuals else None,
        "first_minimum_round": residuals.index(min(residuals)) if residuals else None,
        "non_improving_steps": sum(
            residuals[index] >= residuals[index - 1] for index in range(1, len(residuals))
        ),
        "median_reliability_gap": float(np.median(gaps)) if gaps else None,
        "near_tie_steps_gap_lt_1e_3": sum(gap < 1e-3 for gap in gaps),
        "near_tie_steps_gap_lt_1e_2": sum(gap < 1e-2 for gap in gaps),
    }


def main() -> None:
    corpus = json.loads((ROOT / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
    diagnostics = json.loads((ROOT / "invariant_bpgd_failure_diagnostics.json").read_text(encoding="utf-8"))
    code_lookup = {label: code for label, code in published_primary_panel()}
    corpus_lookup = {case["syndrome_sha256"]: case for case in corpus["cases"]}

    cases = []
    for item in diagnostics["cases"]:
        source = corpus_lookup[item["syndrome_sha256"]]
        code = code_lookup[source["code"]]
        checks = np.asarray(code.hz if source["sector"] == "X" else code.hx, dtype=np.uint8)
        syndrome = np.asarray(source["syndrome"], dtype=np.uint8)
        components = connected_components(checks, syndrome)
        largest = components[0] if components else {"checks": [], "variables": [], "check_count": 0, "variable_count": 0}
        variable_degrees = Counter()
        for check in largest["checks"]:
            for variable in np.flatnonzero(checks[check]):
                variable_degrees[int(variable)] += 1
        four_cycles = count_four_cycles(checks[np.asarray(largest["checks"], dtype=int)] if largest["checks"] else checks[:0], largest["variables"])

        schedule_data = {}
        for schedule, data in item["schedules"].items():
            schedule_data[schedule] = {
                "converged": bool(data["converged"]),
                "decimations": int(data["decimations"]),
                "tie_events": int(data["tie_events"]),
                "zero_llr_events": int(data["zero_llr_events"]),
                "trajectory": trajectory_summary(data["trajectory"]),
            }

        cases.append({
            "syndrome_sha256": item["syndrome_sha256"],
            "code": source["code"],
            "sector": source["sector"],
            "syndrome_weight": int(source["syndrome_weight"]),
            "error_weight": int(source["error_weight"]),
            "component_count": len(components),
            "component_sizes": [component["check_count"] for component in components],
            "largest_component_checks": largest["check_count"],
            "largest_component_variables": largest["variable_count"],
            "largest_component_four_cycles": int(four_cycles),
            "largest_component_max_variable_active_degree": max(variable_degrees.values(), default=0),
            "largest_component_degree_histogram": dict(Counter(variable_degrees.values())),
            "parallel_serial_common_decimation_prefix": item["parallel_serial_common_decimation_prefix"],
            "first_parallel_serial_divergence_round": item["first_parallel_serial_divergence_round"],
            "schedules": schedule_data,
        })

    analysis = {
        "experiment": "invariant_failure_structure_v1",
        "case_count": len(cases),
        "cases": cases,
        "next_tests": [
            "Run BP-OSD and a validated published beam decoder on these exact syndromes.",
            "Test alternate parity-check bases and graph automorphisms.",
            "Record the residual active-check subgraph at each decimation step, not only the input syndrome graph.",
            "Mine additional failures to test whether the same component/cycle signatures recur.",
        ],
        "boundary": (
            "These are descriptive structural metrics on two selected failures. They do not establish a trapping-set theorem or general failure taxonomy."
        ),
    }
    (ROOT / "invariant_failure_structure.json").write_text(
        json.dumps(analysis, indent=2) + "\n", encoding="utf-8"
    )

    lines = ["# Invariant Failure Structural Analysis", ""]
    for case in cases:
        lines += [
            f'## `{case["syndrome_sha256"]}`',
            "",
            f'- Code/sector: **{case["code"]} / {case["sector"]}**',
            f'- Error/syndrome weight: **{case["error_weight"]} / {case["syndrome_weight"]}**',
            f'- Active-check components: **{case["component_count"]}**',
            f'- Component check sizes: `{case["component_sizes"]}`',
            f'- Largest component: **{case["largest_component_checks"]} checks, {case["largest_component_variables"]} variables**',
            f'- Estimated four-cycles in largest active component: **{case["largest_component_four_cycles"]}**',
            f'- Common parallel/serial decision prefix: **{case["parallel_serial_common_decimation_prefix"]}**',
            f'- First schedule divergence: **{case["first_parallel_serial_divergence_round"]}**',
            "",
            "| Schedule | Rounds | Initial residual | Minimum residual | Final residual | Non-improving steps | Median reliability gap |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for schedule, data in case["schedules"].items():
            t = data["trajectory"]
            lines.append(
                f'| {schedule} | {t["rounds"]} | {t["initial_residual"]} | {t["minimum_residual"]} | '
                f'{t["final_residual"]} | {t["non_improving_steps"]} | {t["median_reliability_gap"]:.6g} |'
            )
        lines.append("")
    lines += ["## Next tests", ""] + [f'- {item}' for item in analysis["next_tests"]]
    lines += ["", "## Interpretation boundary", "", analysis["boundary"]]
    (ROOT / "INVARIANT_FAILURE_STRUCTURE.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
