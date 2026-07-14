from __future__ import annotations

"""Reproduce and characterize pure-BPGD nonconvergence cases.

The runner regenerates the fixed 12,000-shot corpus, records baseline failures,
and retries the exact failing syndromes under controlled BP/restart/freeze
variants. It intentionally does not use the syndrome-safe fallback while
classifying pure-BPGD convergence.
"""

import json
from pathlib import Path

import numpy as np
from ldpc import BpDecoder

from bb_code import published_primary_panel


def decode_variant(h, target, *, p, max_iter, epsilon, fresh_decoder, reverse_llr=False):
    h = np.asarray(h, dtype=np.uint8)
    target = np.asarray(target, dtype=np.uint8)
    n = h.shape[1]
    probabilities = np.full(n, p, dtype=float)
    frozen = np.zeros(n, dtype=bool)
    decoder = None

    for step in range(n + 1):
        if fresh_decoder or decoder is None:
            decoder = BpDecoder(
                h,
                error_rate=p,
                max_iter=max_iter,
                bp_method="ms",
                ms_scaling_factor=0.0,
            )
        decoder.update_channel_probs(probabilities)
        output = np.asarray(decoder.decode(target), dtype=np.uint8)
        if np.array_equal((h @ output) & 1, target):
            return True, step

        reliabilities = np.asarray(decoder.log_prob_ratios, dtype=float)
        candidates = np.flatnonzero(~frozen)
        if candidates.size == 0:
            return False, step
        index = int(candidates[np.argmax(np.abs(reliabilities[candidates]))])
        hard_bit = int(reliabilities[index] > 0.0) if reverse_llr else int(reliabilities[index] < 0.0)
        probabilities[index] = 1.0 - epsilon if hard_bit else epsilon
        frozen[index] = True

    return False, n


def main() -> None:
    p = 0.04
    rng = np.random.default_rng(20260714)
    failures = []

    for label, code in published_primary_panel():
        for sector, checks in (("X", code.hz), ("Z", code.hx)):
            h = np.asarray(checks, dtype=np.uint8)
            for shot in range(2000):
                error = (rng.random(code.n) < p).astype(np.uint8)
                syndrome = (h @ error) & 1
                ok, _ = decode_variant(
                    h,
                    syndrome,
                    p=p,
                    max_iter=100,
                    epsilon=1e-9,
                    fresh_decoder=False,
                )
                if not ok:
                    failures.append((label, sector, shot, h, syndrome))

    variants = {
        "baseline_reuse_100_1e-9": dict(max_iter=100, epsilon=1e-9, fresh_decoder=False),
        "fresh_100_1e-9": dict(max_iter=100, epsilon=1e-9, fresh_decoder=True),
        "fresh_150_1e-6": dict(max_iter=150, epsilon=1e-6, fresh_decoder=True),
        "fresh_200_1e-9": dict(max_iter=200, epsilon=1e-9, fresh_decoder=True),
        "fresh_500_1e-6": dict(max_iter=500, epsilon=1e-6, fresh_decoder=True),
        "reverse_llr_fresh_100_1e-9": dict(
            max_iter=100, epsilon=1e-9, fresh_decoder=True, reverse_llr=True
        ),
    }

    results = []
    for name, kwargs in variants.items():
        resolved = 0
        for _, _, _, h, syndrome in failures:
            ok, _ = decode_variant(h, syndrome, p=p, **kwargs)
            resolved += int(ok)
        results.append({
            "variant": name,
            "resolved": resolved,
            "unresolved": len(failures) - resolved,
        })

    payload = {
        "baseline_failure_count": len(failures),
        "failure_locations": [
            {"code": label, "sector": sector, "shot_index": shot}
            for label, sector, shot, _, _ in failures
        ],
        "variant_results": results,
        "warning": "Parameter sensitivity is diagnostic only and does not establish paper fidelity."
    }
    output = Path(__file__).with_name("bpgd_failure_isolation_run.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
