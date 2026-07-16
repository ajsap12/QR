from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from bpgd_adapter import BpgdAdapter, BpgdConfig
from bposd_adapter import BpOsdAdapter, BpOsdConfig
from logical import classify_x_residual


def main() -> None:
    physical_error_rate = 0.04
    shots = 300
    base_seed = 20260714
    records: list[dict[str, object]] = []

    for code_index, (label, code) in enumerate(published_primary_panel()):
        hx = np.asarray(code.hx, dtype=np.uint8)
        hz = np.asarray(code.hz, dtype=np.uint8)
        seed = base_seed + code.l
        rng = np.random.default_rng(seed)
        bposd = BpOsdAdapter(hz, BpOsdConfig(error_rate=physical_error_rate))
        bpgd = BpgdAdapter(hz, BpgdConfig(error_rate=physical_error_rate))

        bposd_logical = 0
        bpgd_logical = 0
        bposd_syndrome_failures = 0
        bpgd_syndrome_failures = 0
        total_decimations = 0
        paired_disagreements = 0
        started = time.perf_counter()

        for _ in range(shots):
            error = (rng.random(code.n) < physical_error_rate).astype(np.uint8)
            syndrome = (hz @ error) & 1

            bposd_correction = np.asarray(bposd.decode(syndrome), dtype=np.uint8)
            bpgd_correction = np.asarray(bpgd.decode(syndrome), dtype=np.uint8)
            total_decimations += bpgd.last_decimations

            bposd_class = classify_x_residual(error ^ bposd_correction, hx, hz)
            bpgd_class = classify_x_residual(error ^ bpgd_correction, hx, hz)

            bposd_logical += bposd_class == "logical_failure"
            bpgd_logical += bpgd_class == "logical_failure"
            bposd_syndrome_failures += bposd_class == "syndrome_failure"
            bpgd_syndrome_failures += bpgd_class == "syndrome_failure"
            paired_disagreements += bposd_class != bpgd_class

        records.append({
            "code": label,
            "n": code.n,
            "k": code.k,
            "physical_error_rate": physical_error_rate,
            "shots": shots,
            "seed": seed,
            "bposd_logical_failures": bposd_logical,
            "bpgd_logical_failures": bpgd_logical,
            "bposd_logical_error_rate": bposd_logical / shots,
            "bpgd_logical_error_rate": bpgd_logical / shots,
            "bposd_syndrome_failures": bposd_syndrome_failures,
            "bpgd_syndrome_failures": bpgd_syndrome_failures,
            "paired_classification_disagreements": paired_disagreements,
            "bpgd_total_decimations": total_decimations,
            "bpgd_mean_decimations": total_decimations / shots,
            "elapsed_seconds": time.perf_counter() - started,
        })

    payload = {
        "experiment": "paired_bp_osd_vs_provisional_bpgd",
        "noise_model": "independent binary X-error code-capacity model",
        "sample_pairing": "Both decoders receive the exact same error and syndrome sample on every shot.",
        "records": records,
        "warning": "The BPGD implementation is independent and provisional; results are integration evidence only, not a faithful-paper reproduction claim."
    }
    output = Path(__file__).with_name("paired_bposd_bpgd_summary.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
