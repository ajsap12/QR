from __future__ import annotations

"""Targeted semantic-variant runner for BPGD failure diagnosis.

The runner is designed to operate on the fixed-seed 12,000-shot corpus and
compare only semantics that remain unresolved after the equation-level tests:
tie handling, update schedule, clipping, and iterations per round.
"""

import json
from pathlib import Path

VARIANTS = [
    {"name": "baseline_parallel_lowest_index", "schedule": "parallel", "tie_break": "lowest_index", "clip": 50.0, "T": 100},
    {"name": "parallel_highest_index", "schedule": "parallel", "tie_break": "highest_index", "clip": 50.0, "T": 100},
    {"name": "parallel_seeded_random_ties", "schedule": "parallel", "tie_break": "seeded_random", "clip": 50.0, "T": 100},
    {"name": "parallel_prior_bit_for_zero_llr", "schedule": "parallel", "tie_break": "prior_bit", "clip": 50.0, "T": 100},
    {"name": "parallel_clip_25", "schedule": "parallel", "tie_break": "lowest_index", "clip": 25.0, "T": 100},
    {"name": "parallel_clip_100", "schedule": "parallel", "tie_break": "lowest_index", "clip": 100.0, "T": 100},
    {"name": "parallel_T_50", "schedule": "parallel", "tie_break": "lowest_index", "clip": 50.0, "T": 50},
    {"name": "parallel_T_200", "schedule": "parallel", "tie_break": "lowest_index", "clip": 50.0, "T": 200},
    {"name": "serial_lowest_index", "schedule": "serial", "tie_break": "lowest_index", "clip": 50.0, "T": 100}
]


def main() -> None:
    payload = {
        "experiment": "bpgd_failure_semantic_variant_plan",
        "status": "runner_manifest_created_execution_pending_engine_support",
        "variants": VARIANTS,
        "required_outputs_per_variant": [
            "total nonconvergence count",
            "overlap with the current 17 stateful failures",
            "new failure count",
            "mean decimations",
            "count of exact or near reliability ties",
            "count of LLR clipping events"
        ],
        "selection_rule": "Adopt no variant merely because it lowers failures; require consistency with the paper or author implementation."
    }
    output = Path(__file__).with_name("failure_semantic_variant_manifest.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
