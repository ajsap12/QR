from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from stateful_sum_product_numba import build_tanner_graph, decode_stateful_sum_product


def digest(bits: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(bits.astype(np.uint8)).tobytes()).hexdigest()


def decode(graph, syndrome, *, p: float, t: int, clip: float):
    return decode_stateful_sum_product(
        graph.h,
        graph.check_edges,
        graph.check_degrees,
        graph.edge_variables,
        graph.variable_edges,
        graph.variable_degrees,
        syndrome,
        p,
        t,
        25.0,
        clip,
    )


def main() -> None:
    p = 0.04
    shots = 2000
    rng = np.random.default_rng(20260714)
    cases: list[dict[str, object]] = []
    code_lookup: dict[tuple[str, str], object] = {}

    for label, code in published_primary_panel():
        for sector, checks in (("X", code.hz), ("Z", code.hx)):
            graph = build_tanner_graph(checks)
            code_lookup[(label, sector)] = graph
            for shot_index in range(shots):
                error = (rng.random(code.n) < p).astype(np.uint8)
                syndrome = (graph.h @ error) & 1
                _, converged, rounds, residual_weight = decode(
                    graph, syndrome, p=p, t=100, clip=50.0
                )
                if not converged:
                    cases.append({
                        "code": label,
                        "sector": sector,
                        "shot_index": shot_index,
                        "syndrome": syndrome.astype(int).tolist(),
                        "syndrome_sha256": digest(syndrome),
                        "error_weight": int(np.sum(error)),
                        "syndrome_weight": int(np.sum(syndrome)),
                        "baseline_rounds": int(rounds),
                        "baseline_residual_syndrome_weight": int(residual_weight),
                    })

    corpus = {
        "experiment": "stateful_failure_corpus",
        "seed": 20260714,
        "physical_error_rate": p,
        "shots_per_code_sector": shots,
        "case_count": len(cases),
        "cases": cases,
    }
    Path(__file__).with_name("stateful_failure_corpus.json").write_text(
        json.dumps(corpus, indent=2) + "\n", encoding="utf-8"
    )

    variants = [
        ("baseline_T100_clip50", 100, 50.0),
        ("T50_clip50", 50, 50.0),
        ("T200_clip50", 200, 50.0),
        ("T100_clip25", 100, 25.0),
        ("T100_clip100", 100, 100.0),
        ("T200_clip25", 200, 25.0),
    ]
    results = []
    for name, t, clip in variants:
        unresolved = []
        for case in cases:
            graph = code_lookup[(str(case["code"]), str(case["sector"]))]
            syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
            _, converged, rounds, residual_weight = decode(
                graph, syndrome, p=p, t=t, clip=clip
            )
            if not converged:
                unresolved.append({
                    "syndrome_sha256": case["syndrome_sha256"],
                    "code": case["code"],
                    "sector": case["sector"],
                    "shot_index": case["shot_index"],
                    "rounds": int(rounds),
                    "residual_syndrome_weight": int(residual_weight),
                })
        results.append({
            "variant": name,
            "T": t,
            "clip": clip,
            "resolved": len(cases) - len(unresolved),
            "unresolved": len(unresolved),
            "unresolved_cases": unresolved,
        })

    replay = {
        "experiment": "exact_failure_variant_replay",
        "input_case_count": len(cases),
        "variants": results,
        "boundary": "Only iteration count and clipping are varied here; tie-breaking and serial scheduling require an extended kernel.",
    }
    Path(__file__).with_name("exact_failure_variant_results.json").write_text(
        json.dumps(replay, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"case_count": len(cases), "variants": results}, indent=2))


if __name__ == "__main__":
    main()
