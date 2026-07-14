from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd


VARIANTS = [
    SemanticConfig(tie_break="lowest_index", zero_llr_policy="zero", schedule="parallel"),
    SemanticConfig(tie_break="highest_index", zero_llr_policy="zero", schedule="parallel"),
    SemanticConfig(tie_break="seeded_random", zero_llr_policy="zero", schedule="parallel", seed=1),
    SemanticConfig(tie_break="lowest_index", zero_llr_policy="one", schedule="parallel"),
    SemanticConfig(tie_break="lowest_index", zero_llr_policy="previous", schedule="parallel"),
    SemanticConfig(tie_break="lowest_index", zero_llr_policy="seeded_random", schedule="parallel", seed=1),
    SemanticConfig(tie_break="lowest_index", zero_llr_policy="zero", schedule="serial"),
]


def variant_name(config: SemanticConfig) -> str:
    return f"{config.schedule}__tie-{config.tie_break}__zero-{config.zero_llr_policy}__seed-{config.seed}"


def main() -> None:
    root = Path(__file__).parent
    corpus = json.loads((root / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
    code_lookup = {}
    for label, code in published_primary_panel():
        code_lookup[(label, "X")] = code.hz
        code_lookup[(label, "Z")] = code.hx

    results = []
    for config in VARIANTS:
        cases = []
        for case in corpus["cases"]:
            checks = code_lookup[(case["code"], case["sector"])]
            decoder = StatefulSemanticBpgd(checks, corpus["physical_error_rate"], config)
            syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
            decoder.decode(syndrome)
            diagnostics = decoder.last_diagnostics
            cases.append({
                "syndrome_sha256": case["syndrome_sha256"],
                "code": case["code"],
                "sector": case["sector"],
                "shot_index": case["shot_index"],
                "converged": diagnostics.converged,
                "decimations": diagnostics.decimations,
                "residual_syndrome_weight": diagnostics.residual_syndrome_weight,
                "tie_events": diagnostics.tie_events,
                "zero_llr_events": diagnostics.zero_llr_events,
                "selected_variables": list(diagnostics.selected_variables),
            })
        results.append({
            "variant": variant_name(config),
            "configuration": {
                "T": config.iterations_per_round,
                "llr_max": config.llr_max,
                "numeric_clip": config.numeric_clip,
                "tie_break": config.tie_break,
                "zero_llr_policy": config.zero_llr_policy,
                "schedule": config.schedule,
                "seed": config.seed,
            },
            "resolved": sum(case["converged"] for case in cases),
            "unresolved": sum(not case["converged"] for case in cases),
            "cases": cases,
        })

    payload = {
        "experiment": "exact_17_case_semantic_replay",
        "input_case_count": len(corpus["cases"]),
        "variants": results,
        "warning": "Diagnostic semantic variants only; no variant is paper-faithful unless supported by the paper or author code."
    }
    (root / "semantic_failure_replay_results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "input_case_count": payload["input_case_count"],
        "summary": [
            {"variant": item["variant"], "resolved": item["resolved"], "unresolved": item["unresolved"]}
            for item in results
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
