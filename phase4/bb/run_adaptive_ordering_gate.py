from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from adaptive_ordering_bpgd import AdaptiveOrderingBpgd, AdaptiveOrderingConfig
from bb_code import published_primary_panel
from build_expanded_failure_corpus import in_rowspace
from run_gate2_controls import run_narrow_beam, run_random_restart, run_serial

ROOT = Path(__file__).parent


def unpack_hex(payload: str, n: int) -> np.ndarray:
    packed = bytes.fromhex(payload)
    return np.unpackbits(np.frombuffer(packed, dtype=np.uint8))[:n].astype(np.uint8)


def adaptive_run(checks: np.ndarray, syndrome: np.ndarray, p: float, budget: int) -> tuple[np.ndarray, dict]:
    decoder = AdaptiveOrderingBpgd(
        checks,
        p,
        AdaptiveOrderingConfig(candidate_budget=budget),
    )
    correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
    d = decoder.last_diagnostics
    a = decoder.last_adaptive
    return correction, {
        "converged": bool(d.converged),
        "decimations": int(d.decimations),
        "residual_syndrome_weight": int(d.residual_syndrome_weight),
        "probe_count": int(a.get("probe_count", 0)),
        "reorder_count": len(a.get("reorder_events", [])),
        "reorder_events": a.get("reorder_events", []),
        "operation_ratio": float((d.decimations + a.get("probe_count", 0)) / max(1, checks.shape[1])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("curated", "train", "validation", "test"), default="curated")
    parser.add_argument("--max-cases", type=int, default=1000)
    args = parser.parse_args()

    code_lookup = {label: code for label, code in published_primary_panel()}
    rows = []

    if args.split == "curated":
        corpus = json.loads((ROOT / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
        source_cases = corpus["cases"][: args.max_cases]
        for index, case in enumerate(source_cases):
            code = code_lookup[case["code"]]
            checks = np.asarray(code.hz if case["sector"] == "X" else code.hx, dtype=np.uint8)
            syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
            p = float(corpus["physical_error_rate"])
            baseline = run_serial(checks, p, syndrome, 20260714, False)
            restart = run_random_restart(checks, p, syndrome, 4, 20260714 + 100 * index)
            beam = run_narrow_beam(checks, p, syndrome, 4)
            adaptive = {}
            for budget in (2, 3, 4):
                _, result = adaptive_run(checks, syndrome, p, budget)
                adaptive[str(budget)] = result
            rows.append({
                "case_id": case["syndrome_sha256"],
                "code": case["code"],
                "sector": case["sector"],
                "baseline": baseline,
                "restart4": restart,
                "beam4": beam,
                "adaptive": adaptive,
            })
    else:
        path = ROOT / "expanded_failure_corpus.jsonl"
        if not path.exists():
            raise FileNotFoundError("Run build_expanded_failure_corpus.py first")
        source_cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        source_cases = [case for case in source_cases if case["split"] == args.split][: args.max_cases]
        for index, case in enumerate(source_cases):
            code = code_lookup[case["code"]]
            if case["sector"] == "X":
                checks = np.asarray(code.hz, dtype=np.uint8)
                stabilizers = np.asarray(code.hx, dtype=np.uint8)
            else:
                checks = np.asarray(code.hx, dtype=np.uint8)
                stabilizers = np.asarray(code.hz, dtype=np.uint8)
            syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
            error = unpack_hex(case["physical_error_packed_hex"], int(case["n"]))
            p = float(case["physical_error_rate"])
            baseline = run_serial(checks, p, syndrome, 20260714, False)
            restart = run_random_restart(checks, p, syndrome, 4, 20260714 + 100 * index)
            beam = run_narrow_beam(checks, p, syndrome, 4)
            baseline["logical_success"] = bool(baseline["converged"] and in_rowspace(error ^ np.asarray(baseline["output"], dtype=np.uint8), stabilizers))
            restart["logical_success"] = bool(restart["converged"] and in_rowspace(error ^ np.asarray(restart["output"], dtype=np.uint8), stabilizers))
            beam["logical_success"] = bool(beam["converged"] and in_rowspace(error ^ np.asarray(beam["output"], dtype=np.uint8), stabilizers))
            adaptive = {}
            for budget in (2, 3, 4):
                correction, result = adaptive_run(checks, syndrome, p, budget)
                result["logical_success"] = bool(result["converged"] and in_rowspace(error ^ correction, stabilizers))
                adaptive[str(budget)] = result
            rows.append({
                "case_id": case["case_id"],
                "code": case["code"],
                "sector": case["sector"],
                "baseline": baseline,
                "restart4": restart,
                "beam4": beam,
                "adaptive": adaptive,
            })

    payload = {
        "experiment": "adaptive_ordering_gate_v1",
        "split": args.split,
        "case_count": len(rows),
        "rows": rows,
        "gate": {
            "go_only_if": [
                "adaptive ordering beats fixed serial on held-out logical success",
                "adaptive ordering matches or beats restart-4 at comparable operation cost",
                "mean operation ratio remains <= 1.5",
            ]
        },
    }
    (ROOT / f"adaptive_ordering_{args.split}_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"split": args.split, "case_count": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
