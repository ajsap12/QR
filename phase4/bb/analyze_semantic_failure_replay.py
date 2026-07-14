from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    data = json.loads((root / "semantic_failure_replay_results.json").read_text(encoding="utf-8"))

    variant_summaries = []
    invariant_unresolved = None
    all_hashes = set()

    for variant in data["variants"]:
        unresolved_cases = [case for case in variant["cases"] if not case["converged"]]
        unresolved_hashes = {case["syndrome_sha256"] for case in unresolved_cases}
        all_hashes |= {case["syndrome_sha256"] for case in variant["cases"]}
        invariant_unresolved = (
            unresolved_hashes
            if invariant_unresolved is None
            else invariant_unresolved & unresolved_hashes
        )
        variant_summaries.append({
            "variant": variant["variant"],
            "resolved": variant["resolved"],
            "unresolved": variant["unresolved"],
            "total_tie_events": sum(case["tie_events"] for case in variant["cases"]),
            "total_zero_llr_events": sum(case["zero_llr_events"] for case in variant["cases"]),
            "mean_decimations": sum(case["decimations"] for case in variant["cases"]) / len(variant["cases"]),
            "unresolved_hashes": sorted(unresolved_hashes),
        })

    resolve_counts = Counter()
    for variant in data["variants"]:
        for case in variant["cases"]:
            if case["converged"]:
                resolve_counts[case["syndrome_sha256"]] += 1

    best_resolved = max(item["resolved"] for item in variant_summaries)
    best_variants = [item["variant"] for item in variant_summaries if item["resolved"] == best_resolved]

    payload = {
        "experiment": "semantic_failure_replay_analysis",
        "input_case_count": data["input_case_count"],
        "variant_count": len(data["variants"]),
        "best_resolved_count": best_resolved,
        "best_variants": best_variants,
        "invariant_unresolved_count": len(invariant_unresolved or set()),
        "invariant_unresolved_hashes": sorted(invariant_unresolved or set()),
        "variant_summaries": variant_summaries,
        "case_resolution_frequency": [
            {
                "syndrome_sha256": syndrome,
                "resolved_by_variant_count": resolve_counts[syndrome],
                "unresolved_by_variant_count": len(data["variants"]) - resolve_counts[syndrome],
            }
            for syndrome in sorted(all_hashes)
        ],
        "decision_rule": "Do not promote a semantic variant solely because it resolves more cases; require consistency with the paper or author code."
    }

    (root / "semantic_failure_replay_analysis.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Semantic Failure Replay Analysis",
        "",
        f"- Exact failure cases: {data['input_case_count']}",
        f"- Semantic variants tested: {len(data['variants'])}",
        f"- Best resolved count: {best_resolved}/{data['input_case_count']}",
        f"- Best variant(s): {', '.join(best_variants)}",
        f"- Cases unresolved by every variant: {len(invariant_unresolved or set())}",
        "",
        "## Variant summary",
        "",
        "| Variant | Resolved | Unresolved | Mean decimations | Tie events | Zero-LLR events |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in variant_summaries:
        lines.append(
            f"| `{item['variant']}` | {item['resolved']} | {item['unresolved']} | "
            f"{item['mean_decimations']:.2f} | {item['total_tie_events']} | {item['total_zero_llr_events']} |"
        )
    lines += [
        "",
        "## Invariant unresolved cases",
        "",
    ]
    if invariant_unresolved:
        lines.extend(f"- `{item}`" for item in sorted(invariant_unresolved))
    else:
        lines.append("No case remained unresolved across all tested semantic variants.")
    lines += [
        "",
        "## Interpretation rule",
        "",
        "A variant is not considered paper-faithful merely because it resolves more failures. "
        "Its tie, zero-LLR, and scheduling behavior must be supported by the paper or author code before promotion.",
    ]
    (root / "SEMANTIC_FAILURE_REPLAY_ANALYSIS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "best_resolved_count": best_resolved,
        "best_variants": best_variants,
        "invariant_unresolved_count": len(invariant_unresolved or set()),
    }, indent=2))


if __name__ == "__main__":
    main()
