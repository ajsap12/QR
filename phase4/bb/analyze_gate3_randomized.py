from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> None:
    path = ROOT / "gate3_randomized_results.json"
    if not path.exists():
        raise FileNotFoundError("Run run_gate3_randomized.py first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload["summary"]
    serial = summary["serial_bpgd"]
    rev = summary["revbpgd"]
    restart = summary["random_restart_bpgd"]
    beam = summary["narrow_beam_bpgd"]

    strongest_control = max(
        (restart, beam),
        key=lambda item: (item["logical_successes"], -item["mean_operations"], -item["p99_operations"]),
    )
    control_name = "random_restart_bpgd" if strongest_control is restart else "narrow_beam_bpgd"

    rev_no_regression = rev["logical_successes"] >= serial["logical_successes"]
    rev_beats_control = (
        rev["logical_successes"] > strongest_control["logical_successes"]
        or (
            rev["logical_successes"] == strongest_control["logical_successes"]
            and rev["mean_operations"] < strongest_control["mean_operations"]
            and rev["p99_operations"] <= strongest_control["p99_operations"]
        )
    )
    rev_memory_advantage = rev["max_peak_checkpoint_bytes"] < beam["max_peak_checkpoint_bytes"]
    gate3_pass = bool(rev_no_regression and rev_beats_control)

    analysis = {
        "gate": "Gate 3 matched hard-case logical validation",
        "case_count": payload["case_count"],
        "strongest_control": control_name,
        "revbpgd_no_regression_vs_serial": rev_no_regression,
        "revbpgd_advantage_vs_strongest_control": rev_beats_control,
        "revbpgd_memory_advantage_vs_beam": rev_memory_advantage,
        "gate3_preliminary_pass": gate3_pass,
        "interpretation": (
            "Proceed to an unfiltered Monte Carlo LER run. RevBPGD has a preliminary matched hard-case advantage."
            if gate3_pass
            else "Do not claim a decoder improvement. RevBPGD did not clear the matched-control gate on this corpus."
        ),
        "boundary": payload["boundary"],
    }
    (ROOT / "gate3_randomized_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Gate 3 Randomized Matched-Case Dashboard",
        "",
        f'- Cases: **{payload["case_count"]}**',
        f'- Split: **{payload["split"]}**',
        f'- Strongest control: **{control_name}**',
        f'- Preliminary gate: **{"PASS" if gate3_pass else "FAIL"}**',
        "",
        "| Decoder | Logical successes | Logical failures | Syndrome converged | Mean ops | p95 ops | p99 ops | Peak checkpoint bytes | Peak states |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("serial_bpgd", "revbpgd", "random_restart_bpgd", "narrow_beam_bpgd"):
        item = summary[name]
        lines.append(
            f'| {name} | {item["logical_successes"]} | {item["logical_failures"]} | '
            f'{item["syndrome_converged"]} | {item["mean_operations"]:.2f} | '
            f'{item["p95_operations"]:.2f} | {item["p99_operations"]:.2f} | '
            f'{item["max_peak_checkpoint_bytes"]} | {item["max_peak_states"]} |'
        )
    lines += [
        "",
        "## Decision checks",
        "",
        f'- No regression versus serial BPGD: **{rev_no_regression}**',
        f'- Advantage versus strongest control: **{rev_beats_control}**',
        f'- Memory advantage versus narrow beam: **{rev_memory_advantage}**',
        "",
        "## Interpretation",
        "",
        analysis["interpretation"],
        "",
        analysis["boundary"],
    ]
    (ROOT / "GATE3_RANDOMIZED_DASHBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
