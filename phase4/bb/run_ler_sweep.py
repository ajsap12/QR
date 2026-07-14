from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from bb_code import published_144_12_instance
from bposd_adapter import BpOsdAdapter, BpOsdConfig
from logical import classify_x_residual


@dataclass(frozen=True)
class SweepPoint:
    physical_error_rate: float
    shots: int
    logical_failures: int
    syndrome_failures: int
    exact_error_matches: int
    logical_error_rate: float
    wilson_95_low: float
    wilson_95_high: float
    elapsed_seconds: float


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    p = successes / trials
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def run_point(error_rate: float, shots: int, seed: int) -> SweepPoint:
    code = published_144_12_instance()
    hx = np.asarray(code.hx, dtype=np.uint8)
    hz = np.asarray(code.hz, dtype=np.uint8)
    decoder = BpOsdAdapter(hz, BpOsdConfig(error_rate=error_rate))
    rng = np.random.default_rng(seed)

    logical_failures = 0
    syndrome_failures = 0
    exact_matches = 0
    started = time.perf_counter()

    for _ in range(shots):
        error = (rng.random(code.n) < error_rate).astype(np.uint8)
        measured_syndrome = (hz @ error) & 1
        correction = np.asarray(decoder.decode(measured_syndrome), dtype=np.uint8)
        residual = error ^ correction
        classification = classify_x_residual(residual, hx, hz)
        logical_failures += classification == "logical_failure"
        syndrome_failures += classification == "syndrome_failure"
        exact_matches += bool(np.array_equal(error, correction))

    elapsed = time.perf_counter() - started
    low, high = wilson_interval(logical_failures, shots)
    return SweepPoint(
        physical_error_rate=error_rate,
        shots=shots,
        logical_failures=logical_failures,
        syndrome_failures=syndrome_failures,
        exact_error_matches=exact_matches,
        logical_error_rate=logical_failures / shots,
        wilson_95_low=low,
        wilson_95_high=high,
        elapsed_seconds=elapsed,
    )


def main() -> None:
    rates = (0.02, 0.04, 0.06, 0.08)
    shots = 500
    base_seed = 20260713
    points = [run_point(rate, shots, base_seed + int(rate * 1000)) for rate in rates]
    payload = {
        "experiment": "preliminary_bp_osd_logical_error_sweep",
        "code": "published BB [[144,12,12]] instance; distance taken from publication, not re-certified here",
        "noise_model": "independent binary X-error code-capacity model",
        "decoder": "ldpc.BpOsdDecoder through BpOsdAdapter",
        "shots_per_point": shots,
        "seed_policy": "20260713 + int(p*1000)",
        "points": [asdict(point) for point in points],
        "warning": "Preliminary integration sweep only; not a threshold estimate or publication-grade benchmark."
    }
    output = Path(__file__).with_name("ler_sweep_summary.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
