from __future__ import annotations

"""Capture immutable per-round traces for pure-BPGD non-convergence cases.

The trace records channel probabilities, selected variable, LLR/reliability,
hard decision, residual syndrome weight, and a SHA-256 digest of the syndrome.
It intentionally disables the BP-OSD fallback.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from ldpc import BpDecoder

from bb_code import published_primary_panel


def digest_bits(bits: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(bits.astype(np.uint8)).tobytes()).hexdigest()


def trace_decode(h: np.ndarray, target: np.ndarray, p: float, max_rounds: int | None = None) -> dict[str, object]:
    n = h.shape[1]
    rounds = max_rounds or n
    llrmax = 25.0
    epsilon = 1.0 / (1.0 + np.exp(llrmax))
    probabilities = np.full(n, p, dtype=float)
    frozen = np.zeros(n, dtype=bool)
    decoder = BpDecoder(
        h,
        error_rate=p,
        max_iter=100,
        bp_method="product_sum",
        schedule="parallel",
    )
    trace = []

    for round_index in range(rounds):
        decoder.update_channel_probs(probabilities)
        output = np.asarray(decoder.decode(target), dtype=np.uint8)
        current = (h @ output) & 1
        residual_weight = int(np.sum(current ^ target))
        llr = np.asarray(decoder.log_prob_ratios, dtype=float)
        entry: dict[str, object] = {
            "round": round_index + 1,
            "residual_syndrome_weight": residual_weight,
            "hard_decision_weight": int(np.sum(output)),
            "undecimated_count": int(np.sum(~frozen)),
        }
        if residual_weight == 0:
            entry["status"] = "converged"
            trace.append(entry)
            return {"converged": True, "trace": trace}

        candidates = np.flatnonzero(~frozen)
        if candidates.size == 0:
            entry["status"] = "all_variables_decimated"
            trace.append(entry)
            break

        selected = int(candidates[np.argmax(np.abs(llr[candidates]))])
        selected_llr = float(llr[selected])
        hard_bit = int(selected_llr < 0.0)
        probabilities[selected] = 1.0 - epsilon if hard_bit else epsilon
        frozen[selected] = True
        entry.update({
            "status": "decimated",
            "selected_variable": selected,
            "selected_llr": selected_llr,
            "selected_reliability": abs(selected_llr),
            "frozen_value": hard_bit,
            "channel_llr_magnitude": llrmax,
        })
        trace.append(entry)

    return {"converged": False, "trace": trace}


def main() -> None:
    p = 0.04
    rng = np.random.default_rng(20260714)
    captured = []

    for label, code in published_primary_panel():
        for sector, checks in (("X", code.hz), ("Z", code.hx)):
            h = np.asarray(checks, dtype=np.uint8)
            for shot_index in range(2000):
                error = (rng.random(code.n) < p).astype(np.uint8)
                syndrome = (h @ error) & 1
                result = trace_decode(h, syndrome, p)
                if not result["converged"]:
                    captured.append({
                        "code": label,
                        "sector": sector,
                        "shot_index": shot_index,
                        "syndrome_sha256": digest_bits(syndrome),
                        "syndrome_weight": int(np.sum(syndrome)),
                        "error_weight": int(np.sum(error)),
                        "rounds": result["trace"],
                    })

    payload = {
        "experiment": "paper_semantic_bpgd_trace_capture",
        "configuration": {
            "p": p,
            "T": 100,
            "bp_method": "product_sum",
            "schedule": "parallel",
            "llrmax": 25,
            "fallback": false
        },
        "case_count": len(captured),
        "cases": captured,
        "warning": "The public ldpc decoder may reset internal messages across decode calls; traces therefore capture package behavior, not yet proven paper-faithful stateful BP."
    }
    output = Path(__file__).with_name("bpgd_trace_capture.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(captured), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
