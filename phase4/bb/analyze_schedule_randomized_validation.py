from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> None:
    payload = json.loads((ROOT / "schedule_randomized_validation.json").read_text(encoding="utf-8"))
    serial = payload["summary"]["serial"]
    parallel = payload["summary"]["parallel"]
    paired = payload["paired_outcomes"]

    serial_advantage = serial["logical_successes"] > parallel["logical_successes"]
    matched_win_balance = paired["serial_only"] - paired["parallel_only"]
    efficient_enough = serial["mean_decimations"] <= parallel["mean_decimations"] * 1.25
    proceed_to_adaptive_scheduler = bool(serial_advantage and matched_win_balance > 0)

    analysis = {
        "gate": "Randomized held-out serial scheduling validation",
        "case_count": payload["case_count"],
        "serial_logical_successes": serial["logical_successes"],
        "parallel_logical_successes": parallel["logical_successes"],
        "serial_only_wins": paired["serial_only"],
        "parallel_only_wins": paired["parallel_only"],
        "matched_win_balance": matched_win_balance,
        "serial_mean_decimations": serial["mean_decimations"],
        "parallel_mean_decimations": parallel["mean_decimations"],
        "serial_advantage": serial_advantage,
        "serial_cost_within_25_percent": efficient_enough,
        "proceed_to_adaptive_scheduler_hypothesis": proceed_to_adaptive_scheduler,
        "interpretation": (
            "The serial advantage generalizes on the held-out enriched hard-case corpus. Proceed to derive and test a state-dependent adaptive ordering rule."
            if proceed_to_adaptive_scheduler
            else "The curated 17-case serial advantage did not generalize strongly enough. Do not claim a new scheduler; retain the trajectory tooling as infrastructure."
        ),
        "boundary": payload["boundary"],
    }
    (ROOT / "schedule_randomized_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Randomized Serial-vs-Parallel Validation",
        "",
        f'- Held-out enriched cases: **{payload["case_count"]}**',
        f'- Serial logical successes: **{serial["logical_successes"]}**',
        f'- Parallel logical successes: **{parallel["logical_successes"]}**',
        f'- Serial-only wins: **{paired["serial_only"]}**',
        f'- Parallel-only wins: **{paired["parallel_only"]}**',
        f'- Mean decimations, serial: **{serial["mean_decimations"]:.2f}**',
        f'- Mean decimations, parallel: **{parallel["mean_decimations"]:.2f}**',
        f'- Proceed to adaptive scheduler hypothesis: **{proceed_to_adaptive_scheduler}**',
        "",
        "## Decision",
        "",
        analysis["interpretation"],
        "",
        analysis["boundary"],
        "",
        "## Scientific meaning",
        "",
        "A positive result would not establish a market-leading decoder by itself. It would establish that update ordering is a reproducible mechanism worth converting into a new state-dependent scheduling rule and benchmarking against Relay-BP, BP-OSD, and search controls.",
    ]
    (ROOT / "SCHEDULE_RANDOMIZED_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
