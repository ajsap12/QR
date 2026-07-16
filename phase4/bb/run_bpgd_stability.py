from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from bpgd_adapter import BpgdAdapter, BpgdConfig


def main() -> None:
    p = 0.04
    shots = 2000
    rng = np.random.default_rng(20260714)
    records: list[dict[str, object]] = []
    started = time.perf_counter()

    for label, code in published_primary_panel():
        for sector, checks in (("X", code.hz), ("Z", code.hx)):
            h = np.asarray(checks, dtype=np.uint8)
            decoder = BpgdAdapter(h, BpgdConfig(error_rate=p, syndrome_safe_fallback=True))
            failures = 0
            fallbacks = 0
            decimations = 0
            for _ in range(shots):
                error = (rng.random(code.n) < p).astype(np.uint8)
                syndrome = (h @ error) & 1
                correction = np.asarray(decoder.decode(syndrome), dtype=np.uint8)
                failures += not np.array_equal((h @ correction) & 1, syndrome)
                fallbacks += decoder.last_diagnostics.fallback_used
                decimations += decoder.last_diagnostics.decimations
            records.append({
                "code": label,
                "sector": sector,
                "shots": shots,
                "syndrome_failures": failures,
                "fallback_uses": fallbacks,
                "mean_decimations": decimations / shots,
            })

    payload = {
        "experiment": "bpgd_syndrome_stability_stress_test",
        "physical_error_rate": p,
        "shots_per_code_sector": shots,
        "total_shots": shots * len(records),
        "records": records,
        "elapsed_seconds": time.perf_counter() - started,
        "warning": "Fallback use must be reported separately; zero returned syndrome failures is not equivalent to pure-BPGD convergence."
    }
    output = Path(__file__).with_name("bpgd_stability_summary.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
