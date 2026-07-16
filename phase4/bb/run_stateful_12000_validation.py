from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from stateful_sum_product_numba import build_tanner_graph, decode_stateful_sum_product


def digest_syndrome(syndrome: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(syndrome).tobytes()).hexdigest()


def main() -> None:
    p = 0.04
    shots = 2000
    rng = np.random.default_rng(20260714)
    records = []
    failures = []

    for label, code in published_primary_panel():
        for sector, checks in (("X", code.hz), ("Z", code.hx)):
            graph = build_tanner_graph(checks)
            nonconvergence = 0
            decimations = 0
            started = time.perf_counter()
            for shot_index in range(shots):
                error = (rng.random(code.n) < p).astype(np.uint8)
                syndrome = (graph.h @ error) & 1
                _, converged, rounds, residual_weight = decode_stateful_sum_product(
                    graph.h,
                    graph.check_edges,
                    graph.check_degrees,
                    graph.edge_variables,
                    graph.variable_edges,
                    graph.variable_degrees,
                    syndrome,
                    p,
                    100,
                    25.0,
                    50.0,
                )
                nonconvergence += not converged
                decimations += rounds
                if not converged:
                    failures.append({
                        "code": label,
                        "sector": sector,
                        "shot_index": shot_index,
                        "syndrome_sha256": digest_syndrome(syndrome),
                        "error_weight": int(np.sum(error)),
                        "syndrome_weight": int(np.sum(syndrome)),
                        "residual_syndrome_weight": int(residual_weight),
                    })
            records.append({
                "code": label,
                "sector": sector,
                "shots": shots,
                "nonconvergence": nonconvergence,
                "mean_decimations": decimations / shots,
                "elapsed_seconds": time.perf_counter() - started,
            })

    payload = {
        "experiment": "optimized_stateful_sum_product_12000_shot_validation",
        "configuration": {
            "physical_error_rate": p,
            "iterations_per_round": 100,
            "llr_max": 25.0,
            "shots_per_code_sector": shots,
            "seed": 20260714,
            "fallback": False,
        },
        "records": records,
        "failure_count": len(failures),
        "failures": failures,
        "warning": "Nonconvergence remains a blocking result; this runner does not claim paper fidelity."
    }
    output = Path(__file__).with_name("stateful_12000_validation_run.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"failure_count": len(failures), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
