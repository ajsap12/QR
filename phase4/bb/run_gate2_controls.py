from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from reversible_bpgd import ReversibleBpgd, ReversibleConfig
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd

ROOT = Path(__file__).parent
RESTART_ATTEMPTS = (1, 2, 4)
BEAM_WIDTHS = (2, 4)
MAX_DEPTH_FACTOR = 2.0


def run_serial(checks: np.ndarray, p: float, syndrome: np.ndarray, seed: int, randomize: bool) -> dict:
    config = SemanticConfig(
        schedule="serial",
        tie_break="random" if randomize else "lowest_index",
        zero_llr_policy="random" if randomize else "zero",
        seed=seed,
    )
    decoder = StatefulSemanticBpgd(checks, p, config)
    output = decoder.decode(syndrome)
    d = decoder.last_diagnostics
    return {
        "converged": bool(d.converged),
        "residual_syndrome_weight": int(d.residual_syndrome_weight),
        "decimations": int(d.decimations),
        "selected_variables": list(d.selected_variables),
        "output": list(output),
        "seed": int(seed),
    }


def run_random_restart(checks: np.ndarray, p: float, syndrome: np.ndarray, attempts: int, seed: int) -> dict:
    runs = []
    total_decimations = 0
    best = None
    for index in range(attempts):
        run = run_serial(checks, p, syndrome, seed + index, randomize=index > 0)
        runs.append(run)
        total_decimations += run["decimations"]
        if best is None or (run["converged"], -run["residual_syndrome_weight"]) > (
            best["converged"], -best["residual_syndrome_weight"]
        ):
            best = run
        if run["converged"]:
            break
    assert best is not None
    return {
        "decoder": "random_restart_bpgd",
        "attempt_budget": attempts,
        "attempts_used": len(runs),
        "converged": bool(best["converged"]),
        "residual_syndrome_weight": int(best["residual_syndrome_weight"]),
        "total_decimations": int(total_decimations),
        "operation_ratio_vs_serial_budget": total_decimations / max(1, checks.shape[1]),
        "runs": runs,
        "output": best["output"],
    }


def run_narrow_beam(checks: np.ndarray, p: float, syndrome: np.ndarray, width: int) -> dict:
    # Explicit parallel-hypothesis control using the same posterior/ranking primitives as RevBPGD.
    base = ReversibleBpgd(
        checks,
        p,
        ReversibleConfig(
            semantic=SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero"),
            max_backtracks=0,
            alternatives_per_decision=2,
            max_total_decimations_factor=MAX_DEPTH_FACTOR,
        ),
    )
    target = np.asarray(syndrome, dtype=np.uint8)
    states = [base._initial_state()]
    total_decimations = 0
    max_total = max(base.n, int(np.ceil(base.n * MAX_DEPTH_FACTOR)))
    best_output = np.zeros(base.n, dtype=np.uint8)
    best_residual = int(np.sum(target))
    peak_states = 1

    while states and total_decimations < max_total:
        next_states = []
        for state in states:
            posterior, output, residual = base._posterior(target, state)
            residual_weight = int(np.sum(residual))
            state.residual_trajectory.append(residual_weight)
            if residual_weight < best_residual:
                best_residual = residual_weight
                best_output = output.copy()
            if residual_weight == 0:
                return {
                    "decoder": "narrow_beam_bpgd",
                    "beam_width": width,
                    "converged": True,
                    "residual_syndrome_weight": 0,
                    "total_decimations": total_decimations,
                    "operation_ratio_vs_serial_budget": total_decimations / max(1, base.n),
                    "peak_states": peak_states,
                    "output": list(map(int, output)),
                }
            ranked = base._rank_candidates(posterior, state.frozen)
            if not ranked:
                continue
            # Primary decision and runner-up variable create distinct live branches.
            branch_specs = [(ranked[0], int(output[ranked[0]]))]
            if len(ranked) > 1:
                branch_specs.append((ranked[1], int(output[ranked[1]])))
            branch_specs.append((ranked[0], 1 - int(output[ranked[0]])))
            for variable, bit in branch_specs:
                child = state.clone()
                child.previous = output.copy()
                base._apply_decision(child, int(variable), int(bit))
                next_states.append((residual_weight, child))
                total_decimations += 1
                if total_decimations >= max_total:
                    break
            if total_decimations >= max_total:
                break
        next_states.sort(key=lambda item: (item[0], len(item[1].selected_variables)))
        states = [item[1] for item in next_states[:width]]
        peak_states = max(peak_states, len(states))

    return {
        "decoder": "narrow_beam_bpgd",
        "beam_width": width,
        "converged": False,
        "residual_syndrome_weight": best_residual,
        "total_decimations": total_decimations,
        "operation_ratio_vs_serial_budget": total_decimations / max(1, base.n),
        "peak_states": peak_states,
        "output": list(map(int, best_output)),
    }


def main() -> None:
    corpus = json.loads((ROOT / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
    lookup = {}
    for label, code in published_primary_panel():
        lookup[(label, "X")] = np.asarray(code.hz, dtype=np.uint8)
        lookup[(label, "Z")] = np.asarray(code.hx, dtype=np.uint8)

    cases = []
    for case_index, case in enumerate(corpus["cases"]):
        checks = lookup[(case["code"], case["sector"])]
        syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
        controls = []
        for attempts in RESTART_ATTEMPTS:
            controls.append(run_random_restart(checks, corpus["physical_error_rate"], syndrome, attempts, 20260714 + 100 * case_index))
        for width in BEAM_WIDTHS:
            controls.append(run_narrow_beam(checks, corpus["physical_error_rate"], syndrome, width))
        cases.append({
            "syndrome_sha256": case["syndrome_sha256"],
            "code": case["code"],
            "sector": case["sector"],
            "controls": controls,
        })

    summary = []
    keys = [("random_restart_bpgd", value) for value in RESTART_ATTEMPTS] + [("narrow_beam_bpgd", value) for value in BEAM_WIDTHS]
    for decoder_name, setting in keys:
        selected = []
        for case in cases:
            for result in case["controls"]:
                if result["decoder"] != decoder_name:
                    continue
                current = result.get("attempt_budget", result.get("beam_width"))
                if current == setting:
                    selected.append(result)
        summary.append({
            "decoder": decoder_name,
            "setting": setting,
            "resolved": sum(bool(item["converged"]) for item in selected),
            "unresolved": sum(not bool(item["converged"]) for item in selected),
            "mean_operation_ratio": float(np.mean([item["operation_ratio_vs_serial_budget"] for item in selected])),
            "max_operation_ratio": float(np.max([item["operation_ratio_vs_serial_budget"] for item in selected])),
        })

    payload = {
        "experiment": "gate2_matched_controls_v1",
        "input_case_count": len(cases),
        "restart_attempts": list(RESTART_ATTEMPTS),
        "beam_widths": list(BEAM_WIDTHS),
        "max_depth_factor": MAX_DEPTH_FACTOR,
        "summary": summary,
        "cases": cases,
        "warning": "Selected failure-corpus controls only. Logical-error and randomized generalization claims require labeled matched samples.",
    }
    (ROOT / "gate2_control_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input_case_count": len(cases), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
