from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

from bb_code import published_primary_panel
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd

TARGET_HASHES = {
    "83cc513e8352f861d464fc57dee727be48466bfc45929f6b528cfe5a79fef44a",
    "bcc41e95e64626fa10ec9313a47460542b4edbefd4e1c4f0a2fab42de9caac5a",
}


def connected_components(h: np.ndarray, check_nodes: set[int], variable_nodes: set[int]) -> list[dict[str, list[int]]]:
    adjacency: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for check in check_nodes:
        key = ("c", check)
        adjacency.setdefault(key, [])
        for variable in np.flatnonzero(h[check]):
            variable = int(variable)
            if variable in variable_nodes:
                adjacency[key].append(("v", variable))
                adjacency.setdefault(("v", variable), []).append(key)

    seen: set[tuple[str, int]] = set()
    output: list[dict[str, list[int]]] = []
    for start in adjacency:
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        checks: list[int] = []
        variables: list[int] = []
        while queue:
            node = queue.popleft()
            if node[0] == "c":
                checks.append(node[1])
            else:
                variables.append(node[1])
            for neighbor in adjacency.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        output.append({"checks": sorted(checks), "variables": sorted(variables)})
    output.sort(key=lambda item: (-(len(item["checks"]) + len(item["variables"])), item["checks"], item["variables"]))
    return output


def count_four_cycles(h: np.ndarray, checks: set[int], variables: set[int]) -> int:
    if not checks or not variables:
        return 0
    h_sub = h[np.array(sorted(checks))][:, np.array(sorted(variables))]
    shared = h_sub.T @ h_sub
    total = 0
    for i in range(shared.shape[0]):
        for j in range(i + 1, shared.shape[1]):
            common = int(shared[i, j])
            total += common * (common - 1) // 2
    return total


def active_region_summary(h: np.ndarray, target: np.ndarray, residual: np.ndarray) -> dict[str, Any]:
    seed_checks = set(int(i) for i in np.flatnonzero(target | residual))
    variables = set()
    for check in seed_checks:
        variables.update(int(v) for v in np.flatnonzero(h[check]))
    checks = set(seed_checks)
    for variable in variables:
        checks.update(int(c) for c in np.flatnonzero(h[:, variable]))
    components = connected_components(h, checks, variables)
    return {
        "seed_check_count": len(seed_checks),
        "expanded_check_count": len(checks),
        "expanded_variable_count": len(variables),
        "component_count": len(components),
        "largest_component_checks": len(components[0]["checks"]) if components else 0,
        "largest_component_variables": len(components[0]["variables"]) if components else 0,
        "four_cycle_count": count_four_cycles(h, checks, variables),
        "components": components,
    }


def traced_decode(h: np.ndarray, error_rate: float, config: SemanticConfig, syndrome: np.ndarray) -> dict[str, Any]:
    decoder = StatefulSemanticBpgd(h, error_rate, config)
    initial_llr = math.log((1.0 - error_rate) / error_rate)
    channel_llr = np.full(decoder.n, initial_llr, dtype=float)
    v2c = channel_llr[decoder.edge_variables].copy()
    c2v = np.zeros(len(decoder.edge_checks), dtype=float)
    frozen = np.zeros(decoder.n, dtype=bool)
    previous = np.zeros(decoder.n, dtype=np.uint8)
    trajectory: list[dict[str, Any]] = []
    selected_variables: list[int] = []
    tie_events = 0
    zero_events = 0

    for round_index in range(decoder.n):
        for _ in range(config.iterations_per_round):
            if config.schedule == "parallel":
                v2c, c2v = decoder._parallel_iteration(syndrome, channel_llr, v2c, c2v)
            else:
                v2c, c2v = decoder._serial_iteration(syndrome, channel_llr, v2c, c2v)
        incoming = np.zeros(decoder.n, dtype=float)
        np.add.at(incoming, decoder.edge_variables, c2v)
        posterior = channel_llr + incoming
        output, zeros = decoder._hard_decisions(posterior, previous)
        zero_events += zeros
        residual = ((h @ output) & 1) ^ syndrome
        residual_weight = int(np.sum(residual))
        selected, tied = decoder._select_variable(posterior, frozen)
        selected_reliability = float(abs(posterior[selected])) if selected >= 0 else None
        second_reliability = None
        reliability_gap = None
        candidates = np.flatnonzero(~frozen)
        if candidates.size >= 2:
            sorted_reliabilities = np.sort(np.abs(posterior[candidates]))[::-1]
            second_reliability = float(sorted_reliabilities[1])
            reliability_gap = float(sorted_reliabilities[0] - sorted_reliabilities[1])
        trajectory.append({
            "round": round_index,
            "residual_syndrome_weight": residual_weight,
            "selected_variable": int(selected),
            "selected_bit": int(output[selected]) if selected >= 0 else None,
            "selected_reliability": selected_reliability,
            "second_reliability": second_reliability,
            "reliability_gap": reliability_gap,
            "tie_event": bool(tied),
            "posterior_abs_min": float(np.min(np.abs(posterior[candidates]))) if candidates.size else None,
            "posterior_abs_median": float(np.median(np.abs(posterior[candidates]))) if candidates.size else None,
            "posterior_abs_max": float(np.max(np.abs(posterior[candidates]))) if candidates.size else None,
        })
        if residual_weight == 0:
            return {
                "converged": True,
                "decimations": round_index,
                "tie_events": tie_events,
                "zero_llr_events": zero_events,
                "selected_variables": selected_variables,
                "trajectory": trajectory,
                "final_output": output.astype(int).tolist(),
                "final_residual": residual.astype(int).tolist(),
                "active_region": active_region_summary(h, syndrome, residual),
            }
        if selected < 0:
            break
        tie_events += int(tied)
        selected_variables.append(int(selected))
        hard_bit = int(output[selected])
        channel_llr[selected] = -config.llr_max if hard_bit else config.llr_max
        frozen[selected] = True
        previous = output

    residual = ((h @ previous) & 1) ^ syndrome
    return {
        "converged": False,
        "decimations": decoder.n,
        "tie_events": tie_events,
        "zero_llr_events": zero_events,
        "selected_variables": selected_variables,
        "trajectory": trajectory,
        "final_output": previous.astype(int).tolist(),
        "final_residual": residual.astype(int).tolist(),
        "active_region": active_region_summary(h, syndrome, residual),
    }


def common_prefix(a: list[int], b: list[int]) -> int:
    count = 0
    for left, right in zip(a, b):
        if left != right:
            break
        count += 1
    return count


def main() -> None:
    root = Path(__file__).parent
    corpus = json.loads((root / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
    code_lookup: dict[tuple[str, str], np.ndarray] = {}
    for label, code in published_primary_panel():
        code_lookup[(label, "X")] = np.asarray(code.hz, dtype=np.uint8)
        code_lookup[(label, "Z")] = np.asarray(code.hx, dtype=np.uint8)

    configs = {
        "parallel": SemanticConfig(tie_break="lowest_index", zero_llr_policy="zero", schedule="parallel"),
        "serial": SemanticConfig(tie_break="lowest_index", zero_llr_policy="zero", schedule="serial"),
    }
    cases_out: list[dict[str, Any]] = []
    for case in corpus["cases"]:
        if case["syndrome_sha256"] not in TARGET_HASHES:
            continue
        h = code_lookup[(case["code"], case["sector"])]
        syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
        schedules = {name: traced_decode(h, corpus["physical_error_rate"], config, syndrome) for name, config in configs.items()}
        prefix = common_prefix(schedules["parallel"]["selected_variables"], schedules["serial"]["selected_variables"])
        cases_out.append({
            "syndrome_sha256": case["syndrome_sha256"],
            "code": case["code"],
            "sector": case["sector"],
            "shot_index": case["shot_index"],
            "error_weight": case["error_weight"],
            "syndrome_weight": case["syndrome_weight"],
            "baseline_residual_syndrome_weight": case["baseline_residual_syndrome_weight"],
            "parallel_serial_common_decimation_prefix": prefix,
            "first_parallel_serial_divergence_round": prefix if prefix < min(len(schedules["parallel"]["selected_variables"]), len(schedules["serial"]["selected_variables"])) else None,
            "schedules": schedules,
        })

    payload = {
        "experiment": "invariant_bpgd_failure_diagnostics",
        "case_count": len(cases_out),
        "cases": cases_out,
        "interpretation_boundary": "Structural and trajectory diagnostics identify hypotheses, not a proof that a named trapping set or pseudocodeword is present.",
    }
    (root / "invariant_bpgd_failure_diagnostics.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Invariant BPGD Failure Diagnostics",
        "",
        "These two syndromes remained unresolved by every tested semantic variant. The report compares parallel and serial schedules and summarizes the active Tanner-graph region.",
        "",
    ]
    for case in cases_out:
        lines += [
            f"## `{case['syndrome_sha256']}`",
            "",
            f"- Code/sector: {case['code']} / {case['sector']}",
            f"- Shot: {case['shot_index']}",
            f"- Injected error weight: {case['error_weight']}",
            f"- Syndrome weight: {case['syndrome_weight']}",
            f"- Parallel/serial common decimation prefix: {case['parallel_serial_common_decimation_prefix']} rounds",
            f"- First schedule divergence: {case['first_parallel_serial_divergence_round']}",
            "",
            "| Schedule | Converged | Final residual | Tie events | Final active checks | Final active variables | 4-cycles in active region |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for schedule_name in ("parallel", "serial"):
            item = case["schedules"][schedule_name]
            region = item["active_region"]
            lines.append(
                f"| {schedule_name} | {item['converged']} | {sum(item['final_residual'])} | {item['tie_events']} | "
                f"{region['expanded_check_count']} | {region['expanded_variable_count']} | {region['four_cycle_count']} |"
            )
        lines += ["", "### Residual trajectory checkpoints", "", "| Round | Parallel residual | Serial residual |", "|---:|---:|---:|"]
        parallel_t = case["schedules"]["parallel"]["trajectory"]
        serial_t = case["schedules"]["serial"]["trajectory"]
        checkpoints = sorted(set([0, 1, 2, 4, 9, 19, 39, 59, 79, 99, len(parallel_t) - 1]))
        for index in checkpoints:
            if 0 <= index < min(len(parallel_t), len(serial_t)):
                lines.append(f"| {index} | {parallel_t[index]['residual_syndrome_weight']} | {serial_t[index]['residual_syndrome_weight']} |")
        lines += [
            "",
            "### Working hypothesis",
            "",
            "The failure is schedule-sensitive but not removed by serial updates. A long shared decimation prefix would indicate that both schedules commit to the same early basin; an early divergence with persistent residual checks would indicate distinct paths reaching different non-solutions. Dense active regions and many 4-cycles support—but do not prove—a short-cycle/trapping-set explanation.",
            "",
        ]
    lines += [
        "## Next falsification test",
        "",
        "Branch at the first low-margin or tied decimation instead of greedily fixing one variable. Test a narrow beam of 2, 4, and 8 branches on only these two syndromes. Resolution by a tiny beam would support the brittle-greedy-decision hypothesis; failure would point toward a deeper representation or update-rule mismatch.",
    ]
    (root / "INVARIANT_BPGD_FAILURE_DIAGNOSTICS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "case_count": len(cases_out),
        "cases": [
            {
                "syndrome_sha256": case["syndrome_sha256"],
                "common_prefix": case["parallel_serial_common_decimation_prefix"],
                "parallel_final_residual": sum(case["schedules"]["parallel"]["final_residual"]),
                "serial_final_residual": sum(case["schedules"]["serial"]["final_residual"]),
            }
            for case in cases_out
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
