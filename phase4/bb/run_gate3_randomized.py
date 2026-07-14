from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from reversible_bpgd import ReversibleBpgd, ReversibleConfig
from run_gate2_controls import run_narrow_beam, run_random_restart
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd

ROOT = Path(__file__).parent


def gf2_rank(matrix: np.ndarray) -> int:
    a = np.asarray(matrix, dtype=np.uint8).copy() & 1
    rank = 0
    for column in range(a.shape[1]):
        pivots = np.flatnonzero(a[rank:, column])
        if pivots.size == 0:
            continue
        pivot = rank + int(pivots[0])
        a[[rank, pivot]] = a[[pivot, rank]]
        for row in range(a.shape[0]):
            if row != rank and a[row, column]:
                a[row] ^= a[rank]
        rank += 1
        if rank == a.shape[0]:
            break
    return rank


def in_rowspace(vector: np.ndarray, generators: np.ndarray) -> bool:
    g = np.asarray(generators, dtype=np.uint8) & 1
    v = np.asarray(vector, dtype=np.uint8).reshape(1, -1) & 1
    return gf2_rank(g) == gf2_rank(np.vstack([g, v]))


def unpack_hex(payload: str, n: int) -> np.ndarray:
    packed = bytes.fromhex(payload)
    return np.unpackbits(np.frombuffer(packed, dtype=np.uint8))[:n].astype(np.uint8)


def logical_success(error: np.ndarray, correction: np.ndarray, stabilizers: np.ndarray, converged: bool) -> bool:
    return bool(converged and in_rowspace(error ^ correction, stabilizers))


def run_serial(checks: np.ndarray, syndrome: np.ndarray, p: float) -> tuple[np.ndarray, dict]:
    decoder = StatefulSemanticBpgd(
        checks,
        p,
        SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero", seed=20260714),
    )
    correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
    d = decoder.last_diagnostics
    return correction, {
        "converged": bool(d.converged),
        "residual_syndrome_weight": int(d.residual_syndrome_weight),
        "decimations": int(d.decimations),
        "operation_count": int(d.decimations),
        "peak_states": 1,
        "peak_checkpoint_bytes": 0,
    }


def run_reversible(checks: np.ndarray, syndrome: np.ndarray, p: float, depth: int) -> tuple[np.ndarray, dict]:
    decoder = ReversibleBpgd(
        checks,
        p,
        ReversibleConfig(
            semantic=SemanticConfig(schedule="serial", tie_break="lowest_index", zero_llr_policy="zero", seed=20260714),
            max_backtracks=depth,
            alternatives_per_decision=2,
            max_total_decimations_factor=2.0,
        ),
    )
    correction, diagnostics = decoder.decode(syndrome)
    correction = np.asarray(correction, dtype=np.uint8)
    state_bytes = int(checks.shape[1] * 4 + checks.shape[0] + checks.size // 8)
    return correction, {
        "converged": bool(diagnostics.converged),
        "residual_syndrome_weight": int(diagnostics.residual_syndrome_weight),
        "decimations": int(diagnostics.total_decimations),
        "operation_count": int(diagnostics.total_decimations),
        "backtracks": int(diagnostics.backtracks),
        "explored_paths": int(diagnostics.explored_paths),
        "peak_states": 1,
        "peak_checkpoint_bytes": int((depth + 1) * state_bytes),
        "residual_trajectory": list(diagnostics.residual_trajectory),
        "selected_variables": list(diagnostics.selected_variables),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gate 3 matched-sample logical validation on the expanded hard-case corpus.")
    parser.add_argument("--split", default="test", choices=("train", "validation", "test", "all"))
    parser.add_argument("--max-cases", type=int, default=1000)
    parser.add_argument("--rev-depth", type=int, default=2)
    parser.add_argument("--restart-attempts", type=int, default=2)
    parser.add_argument("--beam-width", type=int, default=2)
    args = parser.parse_args()

    code_lookup = {label: code for label, code in published_primary_panel()}
    corpus_path = ROOT / "expanded_failure_corpus.jsonl"
    if not corpus_path.exists():
        raise FileNotFoundError("Run build_expanded_failure_corpus.py first")
    cases = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.split != "all":
        cases = [case for case in cases if case["split"] == args.split]
    cases = cases[: args.max_cases]

    output_rows = []
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

        serial_correction, serial = run_serial(checks, syndrome, p)
        serial["logical_success"] = logical_success(error, serial_correction, stabilizers, serial["converged"])

        rev_correction, rev = run_reversible(checks, syndrome, p, args.rev_depth)
        rev["logical_success"] = logical_success(error, rev_correction, stabilizers, rev["converged"])

        restart = run_random_restart(checks, p, syndrome, args.restart_attempts, 20260714)
        restart_correction = np.asarray(restart.pop("output"), dtype=np.uint8)
        restart["operation_count"] = int(restart["total_decimations"])
        restart["peak_states"] = 1
        restart["peak_checkpoint_bytes"] = 0
        restart["logical_success"] = logical_success(error, restart_correction, stabilizers, restart["converged"])

        beam = run_narrow_beam(checks, p, syndrome, args.beam_width)
        beam_correction = np.asarray(beam.pop("output"), dtype=np.uint8)
        beam["operation_count"] = int(beam["total_decimations"])
        beam["peak_checkpoint_bytes"] = int(beam["peak_states"] * checks.shape[1] * 4)
        beam["logical_success"] = logical_success(error, beam_correction, stabilizers, beam["converged"])

        output_rows.append({
            "case_id": case["case_id"],
            "split": case["split"],
            "code": case["code"],
            "sector": case["sector"],
            "physical_error_rate": p,
            "serial_bpgd": serial,
            "revbpgd": rev,
            "random_restart_bpgd": restart,
            "narrow_beam_bpgd": beam,
        })

    summary = {}
    for method in ("serial_bpgd", "revbpgd", "random_restart_bpgd", "narrow_beam_bpgd"):
        records = [row[method] for row in output_rows]
        operations = np.asarray([record["operation_count"] for record in records], dtype=float)
        summary[method] = {
            "cases": len(records),
            "syndrome_converged": int(sum(record["converged"] for record in records)),
            "logical_successes": int(sum(record["logical_success"] for record in records)),
            "logical_failures": int(sum(not record["logical_success"] for record in records)),
            "mean_operations": float(np.mean(operations)) if len(operations) else 0.0,
            "p95_operations": float(np.quantile(operations, 0.95)) if len(operations) else 0.0,
            "p99_operations": float(np.quantile(operations, 0.99)) if len(operations) else 0.0,
            "max_peak_checkpoint_bytes": int(max((record["peak_checkpoint_bytes"] for record in records), default=0)),
            "max_peak_states": int(max((record["peak_states"] for record in records), default=0)),
        }

    win_sets = {}
    for method in summary:
        win_sets[method] = [row["case_id"] for row in output_rows if row[method]["logical_success"]]
    summary["unique_logical_wins"] = {
        method: len(set(wins) - set().union(*(set(other) for key, other in win_sets.items() if key != method)))
        for method, wins in win_sets.items()
    }

    payload = {
        "experiment": "gate3_randomized_matched_hard_cases_v1",
        "split": args.split,
        "max_cases": args.max_cases,
        "rev_depth": args.rev_depth,
        "restart_attempts": args.restart_attempts,
        "beam_width": args.beam_width,
        "case_count": len(output_rows),
        "summary": summary,
        "cases": output_rows,
        "boundary": "This is a matched logical-success comparison on an enriched hard-case corpus. It is not a natural-frequency LER estimate. A later Monte Carlo runner must preserve unfiltered shot frequencies.",
    }
    (ROOT / "gate3_randomized_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(output_rows), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
