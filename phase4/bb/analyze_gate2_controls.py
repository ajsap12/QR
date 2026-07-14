from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> None:
    controls = json.loads((ROOT / "gate2_control_results.json").read_text(encoding="utf-8"))
    gate1_path = ROOT / "reversible_bpgd_gate_analysis.json"
    gate1 = json.loads(gate1_path.read_text(encoding="utf-8")) if gate1_path.exists() else None

    best_control = max(
        controls["summary"],
        key=lambda item: (item["resolved"], -item["mean_operation_ratio"], -item["max_operation_ratio"]),
    )

    rev_best = gate1.get("best_variant") if gate1 else None
    rev_beats_control = None
    if rev_best:
        rev_beats_control = (
            rev_best["resolved"] > best_control["resolved"]
            or (
                rev_best["resolved"] == best_control["resolved"]
                and rev_best["mean_operation_ratio"] < best_control["mean_operation_ratio"]
            )
        )

    analysis = {
        "gate": "Gate 2 preliminary matched controls",
        "input_case_count": controls["input_case_count"],
        "best_control": best_control,
        "revbpgd_best_variant": rev_best,
        "revbpgd_preliminary_advantage": rev_beats_control,
        "interpretation": (
            "RevBPGD shows a preliminary selected-corpus advantage over the implemented controls. Randomized labeled validation is still mandatory."
            if rev_beats_control is True
            else "RevBPGD does not yet show a selected-corpus advantage over the implemented controls. Redesign or stop before expensive randomized work."
            if rev_beats_control is False
            else "Gate 1 analysis was unavailable; controls are summarized without a RevBPGD comparison."
        ),
        "boundary": "This is not a logical-error-rate comparison. It uses a hand-selected failure corpus and operation-count proxies.",
    }
    (ROOT / "gate2_control_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Gate 2 Preliminary Control Dashboard",
        "",
        f'- Selected cases: **{controls["input_case_count"]}**',
        f'- Best control: **{best_control["decoder"]}**, setting **{best_control["setting"]}**',
        f'- Best control resolved: **{best_control["resolved"]}/{controls["input_case_count"]}**',
        f'- Best control mean operation ratio: **{best_control["mean_operation_ratio"]:.3f}×**',
        f'- Best control max operation ratio: **{best_control["max_operation_ratio"]:.3f}×**',
        "",
    ]
    if rev_best:
        lines += [
            "## RevBPGD comparison",
            "",
            f'- RevBPGD best depth: **{rev_best["max_backtracks"]}**',
            f'- RevBPGD resolved: **{rev_best["resolved"]}/{controls["input_case_count"]}**',
            f'- RevBPGD mean operation ratio: **{rev_best["mean_operation_ratio"]:.3f}×**',
            f'- Preliminary advantage: **{rev_beats_control}**',
            "",
        ]
    lines += [
        "## Control summary",
        "",
        "| Decoder | Setting | Resolved | Unresolved | Mean op ratio | Max op ratio |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in controls["summary"]:
        lines.append(
            f'| {item["decoder"]} | {item["setting"]} | {item["resolved"]} | {item["unresolved"]} | '
            f'{item["mean_operation_ratio"]:.3f} | {item["max_operation_ratio"]:.3f} |'
        )
    lines += [
        "",
        "## Interpretation",
        "",
        analysis["interpretation"],
        "",
        analysis["boundary"],
    ]
    (ROOT / "GATE2_CONTROL_DASHBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
