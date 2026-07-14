from __future__ import annotations

import json
import random
import time
from importlib.metadata import version

from bb_code import published_144_12_instance
from bposd_adapter import BpOsdAdapter, BpOsdConfig


def syndrome(h: list[list[int]], error: list[int]) -> tuple[int, ...]:
    return tuple(sum(a * b for a, b in zip(row, error)) & 1 for row in h)


def run(trials: int = 100, error_rate: float = 0.02, seed: int = 20260713) -> dict:
    code = published_144_12_instance()
    decoder = BpOsdAdapter(code.hx, BpOsdConfig(error_rate=error_rate))
    rng = random.Random(seed)
    records = []
    start = time.perf_counter()

    for trial in range(trials):
        error = [1 if rng.random() < error_rate else 0 for _ in range(code.n)]
        target = syndrome(code.hx, error)
        t0 = time.perf_counter()
        correction = decoder.decode(target)
        elapsed = time.perf_counter() - t0
        residual = tuple(a ^ b for a, b in zip(error, correction))
        records.append(
            {
                "trial": trial,
                "error_weight": sum(error),
                "correction_weight": sum(correction),
                "syndrome_matched": syndrome(code.hx, list(correction)) == target,
                "residual_syndrome_zero": not any(syndrome(code.hx, list(residual))),
                "exact_match": tuple(error) == correction,
                "decode_seconds": elapsed,
            }
        )

    total = time.perf_counter() - start
    return {
        "ldpc_version": version("ldpc"),
        "code": {"l": code.l, "m": code.m, "n": code.n, "k": code.k},
        "noise_model": "independent_binary_code_capacity",
        "error_rate": error_rate,
        "trials": trials,
        "seed": seed,
        "syndrome_match_count": sum(r["syndrome_matched"] for r in records),
        "residual_syndrome_zero_count": sum(r["residual_syndrome_zero"] for r in records),
        "exact_error_match_count": sum(r["exact_match"] for r in records),
        "mean_decode_seconds": sum(r["decode_seconds"] for r in records) / trials,
        "max_decode_seconds": max(r["decode_seconds"] for r in records),
        "total_seconds": total,
        "warning": "Smoke integration test only; logical error rate is not computed.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
