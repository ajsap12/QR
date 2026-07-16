from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from bposd_adapter import BpOsdAdapter, BpOsdConfig
from logical import classify_x_residual


def wilson_interval(failures: int, shots: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = failures / shots
    denominator = 1.0 + z * z / shots
    center = (p + z * z / (2.0 * shots)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / shots + z * z / (4.0 * shots * shots)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def run_sector(code, sector: str, error_rate: float, seed: int) -> dict[str, object]:
    if sector == "X":
        syndrome_checks = np.asarray(code.hz, dtype=np.uint8)
        stabilizer_checks = np.asarray(code.hx, dtype=np.uint8)
    elif sector == "Z":
        syndrome_checks = np.asarray(code.hx, dtype=np.uint8)
        stabilizer_checks = np.asarray(code.hz, dtype=np.uint8)
    else:
        raise ValueError("sector must be X or Z")

    decoder = BpOsdAdapter(syndrome_checks, BpOsdConfig(error_rate=error_rate))
    rng = np.random.default_rng(seed)
    shots = 0
    logical_failures = 0
    syndrome_failures = 0
    min_failures = 50
    max_shots = 2000
    batch_size = 100
    started = time.perf_counter()

    while shots < max_shots and logical_failures < min_failures:
        current_batch = min(batch_size, max_shots - shots)
        for _ in range(current_batch):
            error = (rng.random(code.n) < error_rate).astype(np.uint8)
            measured = (syndrome_checks @ error) & 1
            correction = np.asarray(decoder.decode(measured), dtype=np.uint8)
            residual = error ^ correction
            classification = classify_x_residual(residual, stabilizer_checks, syndrome_checks)
            logical_failures += classification == "logical_failure"
            syndrome_failures += classification == "syndrome_failure"
        shots += current_batch

    low, high = wilson_interval(logical_failures, shots)
    return {
        "sector": sector,
        "physical_error_rate": error_rate,
        "shots": shots,
        "logical_failures": logical_failures,
        "syndrome_failures": syndrome_failures,
        "logical_error_rate": logical_failures / shots,
        "wilson_95_low": low,
        "wilson_95_high": high,
        "elapsed_seconds": time.perf_counter() - started,
        "stop_reason": "minimum_failures_reached" if logical_failures >= min_failures else "maximum_shots_reached",
    }


def main() -> None:
    rates = (0.02, 0.04, 0.06)
    base_seed = 20260714
    records: list[dict[str, object]] = []

    for code_index, (label, code) in enumerate(published_primary_panel()):
        for sector_index, sector in enumerate(("X", "Z")):
            for error_rate in rates:
                seed = base_seed + code_index * 10000 + sector_index * 5000 + int(error_rate * 1000)
                result = run_sector(code, sector, error_rate, seed)
                records.append({
                    "code": label,
                    "n": code.n,
                    "k": code.k,
                    "seed": seed,
                    **result,
                })

    payload = {
        "experiment": "adaptive_multi_code_multi_sector_bp_osd_panel",
        "noise_model": "independent binary code-capacity noise, evaluated separately in X and Z sectors",
        "decoder": "ldpc.BpOsdDecoder through BpOsdAdapter",
        "adaptive_rule": "100-shot batches until >=50 logical failures or 2000 shots",
        "records": records,
        "warning": "Bounded integration panel only; not a threshold estimate and not a depolarizing-noise decoder comparison."
    }
    output = Path(__file__).with_name("adaptive_panel_summary.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
