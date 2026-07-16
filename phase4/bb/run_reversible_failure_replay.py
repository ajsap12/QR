from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from reversible_bpgd import ReversibleBpgd, ReversibleConfig
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd


DEPTHS = (0, 1, 2, 4)


def run_serial(checks: np.ndarray, error_rate: float, syndrome: np.ndarray) -> dict:
    config = SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero")
    decoder = StatefulSemanticBpgd(checks, error_rate, config)
    output = decoder.decode(syndrome)
    diagnostics = decoder.last_diagnostics
    return {
        "decoder": "serial_bpgd",
        "max_backtracks": 0,
        "converged": diagnostics.converged,
        "residual_syndrome_weight": diagnostics.residual_syndrome_weight,
        "total_decimations": diagnostics.decimations,
        "explored_paths": 1,
        "backtracks_used": 0,
        "rollback_rounds": [],
        "selected_variables": list(diagnostics.selected_variables),
        "residual_trajectory": [],
        "operation_ratio_vs_serial_budget": diagnostics.decimations / max(1, checks.shape[1]),
        "output": list(output),
    }


def run_reversible(checks: np.ndarray, error_rate: float, syndrome: np.ndarray, depth: int) -> dict:
    config = ReversibleConfig(
        semantic=SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero"),
        max_backtracks=depth,
        alternatives_per_decision=2,
        stall_window=4,
        min_residual_improvement=1,
        max_total_decimations_factor=2.0,
    )
    decoder = ReversibleBpgd(checks, error_rate, config)
    output = decoder.decode(syndrome)
    diagnostics = decoder.last_diagnostics
    return {
        "decoder": "reversible_bpgd",
        "max_backtracks": depth,
        "converged": diagnostics.converged,
        "residual_syndrome_weight": diagnostics.residual_syndrome_weight,
        "total_decimations": diagnostics.total_decimations,
        "explored_paths": diagnostics.explored_paths,
        "backtracks_used": diagnostics.backtracks_used,
        "rollback_rounds": list(diagnostics.rollback_rounds),
        "selected_variables": list(diagnostics.selected_variables),
        "residual_trajectory": list(diagnostics.residual_trajectory),
        "operation_ratio_vs_serial_budget": diagnostics.operation_ratio_vs_serial_budget,
        "output": list(output),
    }


def main() -> None:
    root = Path(__file__).parent
    corpus = json.loads((root / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
    code_lookup: dict[tuple[str, str], np.ndarray] = {}
    for label, code in published_primary_panel():
        code_lookup[(label, "X")] = np.asarray(code.hz, dtype=np.uint8)
        code_lookup[(label, "Z")] = np.asarray(code.hx, dtype=np.uint8)

    cases = []
    for case in corpus["cases"]:
        checks = code_lookup[(case["code"], case["sector"])]
        syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
        variants = [run_serial(checks, corpus["physical_error_rate"], syndrome)]
        for depth in DEPTHS[1:]:
            variants.append(run_reversible(checks, corpus["physical_error_rate"], syndrome, depth))
        cases.append({
            "syndrome_sha256": case["syndrome_sha256"],
            "code": case["code"],
            "sector": case["sector"],
            "shot_index": case["shot_index"],
            "error_weight": case.get("error_weight"),
            "syndrome_weight": case.get("syndrome_weight"),
            "variants": variants,
        })

    summaries = []
    for depth in DEPTHS:
        key = "serial_bpgd" if depth == 0 else "reversible_bpgd"
        selected = [
            variant
            for case in cases
            for variant in case["variants"]
            if variant["decoder"] == key and variant["max_backtracks"] == depth
        ]
        summaries.append({
            "decoder": key,
            "max_backtracks": depth,
            "resolved": sum(item["converged"] for item in selected),
            "unresolved": sum(not item["converged"] for item in selected),
            "mean_operation_ratio": float(np.mean([item["operation_ratio_vs_serial_budget"] for item in selected])),
            "max_operation_ratio": float(np.max([item["operation_ratio_vs_serial_budget"] for item in selected])),
            "mean_backtracks": float(np.mean([item["backtracks_used"] for item in selected])),
        })

    payload = {
        "experiment": "reversible_bpgd_gate_1",
        "input_case_count": len(cases),
        "configuration": {
            "depths": list(DEPTHS),
            "schedule": "serial",
            "alternatives_per_decision": 2,
            "stall_window": 4,
            "max_total_decimations_factor": 2.0,
        },
        "summary": summaries,
        "cases": cases,
        "warning": "Selected failure-corpus gate only; passing this gate does not establish randomized LER improvement or novelty.",
    }
    (root / "reversible_bpgd_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input_case_count": len(cases), "summary": summaries}, indent=2))


if __name__ == "__main__":
    main()
