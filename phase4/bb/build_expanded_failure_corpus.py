from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np

from bb_code import published_primary_panel
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd
from stateful_sum_product_numba import build_tanner_graph, decode_stateful_sum_product


ROOT = Path(__file__).parent
DEFAULT_RATES = (0.02, 0.03, 0.04)
DEFAULT_SEED = 20260714


def digest(bits: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(bits.astype(np.uint8)).tobytes()).hexdigest()


def packed_hex(bits: np.ndarray) -> str:
    return np.packbits(bits.astype(np.uint8)).tobytes().hex()


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


def deterministic_split(case_hash: str) -> str:
    value = int(case_hash[:8], 16) % 100
    if value < 70:
        return "train"
    if value < 85:
        return "validation"
    return "test"


def fast_bp_decode(graph, syndrome: np.ndarray, p: float):
    return decode_stateful_sum_product(
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


def classify_case(*, fast_converged: bool, serial_converged: bool, decimations: int, n: int) -> str:
    if not serial_converged:
        return "serial_bpgd_nonconvergence"
    if not fast_converged and decimations >= max(8, n // 2):
        return "late_serial_recovery"
    if not fast_converged:
        return "fast_bp_nonconvergence_serial_recovery"
    return "hard_high_decimation"


def parse_rates(value: str) -> tuple[float, ...]:
    rates = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    if not rates or any(not 0.0 < rate < 0.5 for rate in rates):
        raise argparse.ArgumentTypeError("rates must be comma-separated values between 0 and 0.5")
    return rates


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine a deduplicated, labeled BB-decoder failure corpus.")
    parser.add_argument("--shots", type=int, default=int(os.getenv("QR_CORPUS_SHOTS", "1000")), help="shots per code/sector/rate")
    parser.add_argument("--rates", type=parse_rates, default=DEFAULT_RATES, help="comma-separated physical error rates")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-cases-per-stratum", type=int, default=int(os.getenv("QR_CORPUS_MAX_CASES", "500")))
    parser.add_argument("--hard-decimation-fraction", type=float, default=0.50)
    args = parser.parse_args()

    if args.shots <= 0:
        raise ValueError("shots must be positive")
    if args.max_cases_per_stratum <= 0:
        raise ValueError("max-cases-per-stratum must be positive")

    rng = np.random.default_rng(args.seed)
    seen: set[str] = set()
    cases: list[dict[str, object]] = []
    counters: Counter[str] = Counter()
    strata_counts: defaultdict[tuple[str, str, float, str], int] = defaultdict(int)

    serial_config = SemanticConfig(
        schedule="serial",
        tie_break="lowest_index",
        zero_llr_policy="zero",
        seed=args.seed,
    )

    for code_label, code in published_primary_panel():
        sectors = (
            ("X", np.asarray(code.hz, dtype=np.uint8), np.asarray(code.hx, dtype=np.uint8)),
            ("Z", np.asarray(code.hx, dtype=np.uint8), np.asarray(code.hz, dtype=np.uint8)),
        )
        for sector, checks, stabilizers in sectors:
            graph = build_tanner_graph(checks)
            for p in args.rates:
                for shot_index in range(args.shots):
                    counters["shots_total"] += 1
                    error = (rng.random(code.n) < p).astype(np.uint8)
                    syndrome = (checks @ error) & 1
                    syndrome_hash = digest(syndrome)

                    fast_correction, fast_converged, fast_rounds, fast_residual = fast_bp_decode(graph, syndrome, p)
                    fast_correction = np.asarray(fast_correction, dtype=np.uint8)

                    # Mine all fast-BP failures and unusually expensive serial recoveries.
                    serial_decoder = StatefulSemanticBpgd(checks, p, serial_config)
                    serial_correction = np.asarray(serial_decoder.decode(syndrome), dtype=np.uint8)
                    diagnostics = serial_decoder.last_diagnostics
                    hard_threshold = max(8, int(code.n * args.hard_decimation_fraction))
                    is_hard = (not fast_converged) or (not diagnostics.converged) or diagnostics.decimations >= hard_threshold
                    if not is_hard:
                        continue

                    counters["hard_candidates"] += 1
                    case_key = f"{code_label}|{sector}|{p:.8g}|{syndrome_hash}"
                    case_hash = hashlib.sha256(case_key.encode("utf-8")).hexdigest()
                    if case_hash in seen:
                        counters["duplicates_skipped"] += 1
                        continue

                    category = classify_case(
                        fast_converged=bool(fast_converged),
                        serial_converged=diagnostics.converged,
                        decimations=diagnostics.decimations,
                        n=code.n,
                    )
                    stratum = (code_label, sector, float(p), category)
                    if strata_counts[stratum] >= args.max_cases_per_stratum:
                        counters["stratum_cap_skipped"] += 1
                        continue

                    seen.add(case_hash)
                    strata_counts[stratum] += 1
                    residual_error = error ^ serial_correction
                    serial_logical_success = bool(
                        diagnostics.converged and in_rowspace(residual_error, stabilizers)
                    )
                    fast_logical_success = bool(
                        fast_converged and in_rowspace(error ^ fast_correction, stabilizers)
                    )

                    cases.append({
                        "case_id": case_hash,
                        "split": deterministic_split(case_hash),
                        "code": code_label,
                        "n": int(code.n),
                        "k": int(code.k),
                        "sector": sector,
                        "physical_error_rate": float(p),
                        "seed": int(args.seed),
                        "shot_index": int(shot_index),
                        "syndrome_sha256": syndrome_hash,
                        "syndrome": syndrome.astype(int).tolist(),
                        "syndrome_weight": int(np.sum(syndrome)),
                        "physical_error_packed_hex": packed_hex(error),
                        "physical_error_weight": int(np.sum(error)),
                        "fast_bp": {
                            "converged": bool(fast_converged),
                            "rounds": int(fast_rounds),
                            "residual_syndrome_weight": int(fast_residual),
                            "logical_success": fast_logical_success,
                            "correction_packed_hex": packed_hex(fast_correction),
                        },
                        "serial_bpgd": {
                            "converged": bool(diagnostics.converged),
                            "decimations": int(diagnostics.decimations),
                            "residual_syndrome_weight": int(diagnostics.residual_syndrome_weight),
                            "tie_events": int(diagnostics.tie_events),
                            "zero_llr_events": int(diagnostics.zero_llr_events),
                            "selected_variables": list(diagnostics.selected_variables),
                            "logical_success": serial_logical_success,
                            "correction_packed_hex": packed_hex(serial_correction),
                        },
                        "failure_category": category,
                    })
                    counters[f"category:{category}"] += 1

    cases.sort(key=lambda item: str(item["case_id"]))
    metadata = {
        "experiment": "expanded_bb_failure_corpus_v1",
        "schema_version": 1,
        "seed": int(args.seed),
        "rates": list(args.rates),
        "shots_per_code_sector_rate": int(args.shots),
        "max_cases_per_stratum": int(args.max_cases_per_stratum),
        "hard_decimation_fraction": float(args.hard_decimation_fraction),
        "case_count": len(cases),
        "counters": dict(counters),
        "split_counts": dict(Counter(str(case["split"]) for case in cases)),
        "category_counts": dict(Counter(str(case["failure_category"]) for case in cases)),
        "boundary": "This corpus is mined with fast BP and serial semantic BPGD. It contains logical-success labels derived from CSS stabilizer row-space membership. It is not a representative estimate of natural syndrome frequency because hard cases are deliberately selected and capped by stratum.",
    }

    jsonl_path = ROOT / "expanded_failure_corpus.jsonl"
    jsonl_path.write_text("".join(json.dumps(case, sort_keys=True) + "\n" for case in cases), encoding="utf-8")
    (ROOT / "expanded_failure_corpus_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
