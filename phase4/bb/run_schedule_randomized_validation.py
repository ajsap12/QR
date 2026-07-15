from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from build_expanded_failure_corpus import in_rowspace
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd

ROOT = Path(__file__).parent


def unpack_hex(payload: str, n: int) -> np.ndarray:
    packed = bytes.fromhex(payload)
    return np.unpackbits(np.frombuffer(packed, dtype=np.uint8))[:n].astype(np.uint8)


def run_decoder(checks: np.ndarray, syndrome: np.ndarray, p: float, schedule: str) -> tuple[np.ndarray, dict]:
    decoder = StatefulSemanticBpgd(
        checks,
        p,
        SemanticConfig(
            schedule=schedule,
            tie_break="lowest_index",
            zero_llr_policy="zero",
            seed=20260714,
        ),
    )
    correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
    d = decoder.last_diagnostics
    return correction, {
        "converged": bool(d.converged),
        "decimations": int(d.decimations),
        "residual_syndrome_weight": int(d.residual_syndrome_weight),
        "tie_events": int(d.tie_events),
        "zero_llr_events": int(d.zero_llr_events),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare serial and parallel BPGD on held-out expanded hard cases.")
    parser.add_argument("--split", choices=("train", "validation", "test", "all"), default="test")
    parser.add_argument("--max-cases", type=int, default=1000)
    args = parser.parse_args()

    corpus_path = ROOT / "expanded_failure_corpus.jsonl"
    if not corpus_path.exists():
        raise FileNotFoundError("Run build_expanded_failure_corpus.py first")
    cases = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.split != "all":
        cases = [case for case in cases if case["split"] == args.split]
    cases = cases[: args.max_cases]

    code_lookup = {label: code for label, code in published_primary_panel()}
    rows = []
    for case in cases:
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

        result = {}
        for schedule in ("serial", "parallel"):
            correction, diagnostics = run_decoder(checks, syndrome, p, schedule)
            diagnostics["logical_success"] = bool(
                diagnostics["converged"] and in_rowspace(error ^ correction, stabilizers)
            )
            result[schedule] = diagnostics

        rows.append({
            "case_id": case["case_id"],
            "code": case["code"],
            "sector": case["sector"],
            "physical_error_rate": p,
            "failure_category": case["failure_category"],
            "serial": result["serial"],
            "parallel": result["parallel"],
        })

    summary = {}
    for schedule in ("serial", "parallel"):
        records = [row[schedule] for row in rows]
        decimations = np.asarray([item["decimations"] for item in records], dtype=float)
        summary[schedule] = {
            "cases": len(records),
            "converged": int(sum(item["converged"] for item in records)),
            "logical_successes": int(sum(item["logical_success"] for item in records)),
            "logical_failures": int(sum(not item["logical_success"] for item in records)),
            "mean_decimations": float(np.mean(decimations)) if len(decimations) else 0.0,
            "p95_decimations": float(np.quantile(decimations, 0.95)) if len(decimations) else 0.0,
            "p99_decimations": float(np.quantile(decimations, 0.99)) if len(decimations) else 0.0,
        }

    serial_only = [row["case_id"] for row in rows if row["serial"]["logical_success"] and not row["parallel"]["logical_success"]]
    parallel_only = [row["case_id"] for row in rows if row["parallel"]["logical_success"] and not row["serial"]["logical_success"]]
    both = [row["case_id"] for row in rows if row["parallel"]["logical_success"] and row["serial"]["logical_success"]]
    neither = [row["case_id"] for row in rows if not row["parallel"]["logical_success"] and not row["serial"]["logical_success"]]

    payload = {
        "experiment": "serial_parallel_randomized_validation_v1",
        "split": args.split,
        "max_cases": args.max_cases,
        "case_count": len(rows),
        "summary": summary,
        "paired_outcomes": {
            "serial_only": len(serial_only),
            "parallel_only": len(parallel_only),
            "both": len(both),
            "neither": len(neither),
            "serial_only_case_ids": serial_only,
            "parallel_only_case_ids": parallel_only,
        },
        "cases": rows,
        "boundary": "This is a held-out comparison on an enriched hard-case corpus. It does not estimate natural-frequency logical error rates.",
    }
    (ROOT / "schedule_randomized_validation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(rows), "summary": summary, "paired_outcomes": payload["paired_outcomes"]}, indent=2))


if __name__ == "__main__":
    main()
