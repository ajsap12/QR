from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from bb_code import published_primary_panel
from stateful_semantic_kernel import SemanticConfig, StatefulSemanticBpgd

ROOT = Path(__file__).parent
SCHEDULES = ("serial", "parallel")


def reliability_gap(posterior: np.ndarray, frozen: np.ndarray) -> float | None:
    candidates = np.flatnonzero(~frozen)
    if candidates.size < 2:
        return None
    values = np.sort(np.abs(posterior[candidates]))
    return float(values[-1] - values[-2])


def capture_trajectory(checks: np.ndarray, syndrome: np.ndarray, p: float, schedule: str) -> dict:
    config = SemanticConfig(
        schedule=schedule,
        tie_break="lowest_index",
        zero_llr_policy="zero",
        seed=20260714,
    )
    decoder = StatefulSemanticBpgd(checks, p, config)
    target = np.asarray(syndrome, dtype=np.uint8)
    initial_llr = math.log((1.0 - p) / p)
    channel_llr = np.full(decoder.n, initial_llr, dtype=float)
    v2c = channel_llr[decoder.edge_variables].copy()
    c2v = np.zeros(len(decoder.edge_checks), dtype=float)
    frozen = np.zeros(decoder.n, dtype=bool)
    previous = np.zeros(decoder.n, dtype=np.uint8)
    trajectory: list[dict[str, object]] = []
    tie_events = 0
    zero_events = 0

    for round_index in range(decoder.n):
        for _ in range(config.iterations_per_round):
            if schedule == "parallel":
                v2c, c2v = decoder._parallel_iteration(target, channel_llr, v2c, c2v)
            else:
                v2c, c2v = decoder._serial_iteration(target, channel_llr, v2c, c2v)

        incoming = np.zeros(decoder.n, dtype=float)
        np.add.at(incoming, decoder.edge_variables, c2v)
        posterior = channel_llr + incoming
        output, zeros = decoder._hard_decisions(posterior, previous)
        zero_events += int(zeros)
        residual = ((decoder.h @ output) & 1) ^ target
        residual_weight = int(np.sum(residual))
        selected, tied = decoder._select_variable(posterior, frozen)
        if selected >= 0:
            tie_events += int(tied)
        candidates = np.flatnonzero(~frozen)
        abs_candidates = np.abs(posterior[candidates]) if candidates.size else np.asarray([], dtype=float)
        changed_bits = int(np.sum(output != previous))
        step = {
            "round": round_index,
            "residual_syndrome_weight": residual_weight,
            "unsatisfied_checks": np.flatnonzero(residual).astype(int).tolist(),
            "selected_variable": int(selected) if selected >= 0 else None,
            "selected_hard_bit": int(output[selected]) if selected >= 0 else None,
            "selected_reliability": float(abs(posterior[selected])) if selected >= 0 else None,
            "reliability_gap": reliability_gap(posterior, frozen),
            "mean_candidate_reliability": float(np.mean(abs_candidates)) if abs_candidates.size else None,
            "min_candidate_reliability": float(np.min(abs_candidates)) if abs_candidates.size else None,
            "max_candidate_reliability": float(np.max(abs_candidates)) if abs_candidates.size else None,
            "changed_hard_decisions": changed_bits,
            "frozen_count": int(np.sum(frozen)),
            "tie_event": bool(tied) if selected >= 0 else False,
            "zero_llr_events_this_round": int(zeros),
        }
        trajectory.append(step)
        if residual_weight == 0:
            return {
                "schedule": schedule,
                "converged": True,
                "decimations": round_index,
                "residual_syndrome_weight": 0,
                "tie_events": tie_events,
                "zero_llr_events": zero_events,
                "trajectory": trajectory,
                "output": output.astype(int).tolist(),
            }
        if selected < 0:
            break
        hard_bit = int(output[selected])
        channel_llr[selected] = -config.llr_max if hard_bit else config.llr_max
        frozen[selected] = True
        previous = output.copy()

    final_residual = int(np.sum((((decoder.h @ previous) & 1) ^ target)))
    return {
        "schedule": schedule,
        "converged": False,
        "decimations": decoder.n,
        "residual_syndrome_weight": final_residual,
        "tie_events": tie_events,
        "zero_llr_events": zero_events,
        "trajectory": trajectory,
        "output": previous.astype(int).tolist(),
    }


def main() -> None:
    corpus = json.loads((ROOT / "stateful_failure_corpus.json").read_text(encoding="utf-8"))
    lookup: dict[tuple[str, str], np.ndarray] = {}
    for label, code in published_primary_panel():
        lookup[(label, "X")] = np.asarray(code.hz, dtype=np.uint8)
        lookup[(label, "Z")] = np.asarray(code.hx, dtype=np.uint8)

    cases = []
    for case in corpus["cases"]:
        checks = lookup[(case["code"], case["sector"])]
        syndrome = np.asarray(case["syndrome"], dtype=np.uint8)
        schedules = {
            schedule: capture_trajectory(checks, syndrome, float(corpus["physical_error_rate"]), schedule)
            for schedule in SCHEDULES
        }
        cases.append({
            "syndrome_sha256": case["syndrome_sha256"],
            "code": case["code"],
            "sector": case["sector"],
            "shot_index": case["shot_index"],
            "syndrome_weight": int(np.sum(syndrome)),
            "schedules": schedules,
        })

    payload = {
        "experiment": "serial_parallel_trajectory_capture_v1",
        "input_case_count": len(cases),
        "physical_error_rate": corpus["physical_error_rate"],
        "cases": cases,
        "boundary": "Selected 17-case failure corpus only. Results establish mechanisms on curated hard cases, not natural-frequency decoder performance.",
    }
    (ROOT / "schedule_trajectory_results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "input_case_count": len(cases),
        "serial_converged": sum(case["schedules"]["serial"]["converged"] for case in cases),
        "parallel_converged": sum(case["schedules"]["parallel"]["converged"] for case in cases),
    }, indent=2))


if __name__ == "__main__":
    main()
