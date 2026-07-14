from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).parent


def main() -> None:
    corpus_path = ROOT / "expanded_failure_corpus.jsonl"
    metadata_path = ROOT / "expanded_failure_corpus_metadata.json"
    if not corpus_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Run build_expanded_failure_corpus.py first")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    ids = [case["case_id"] for case in cases]
    duplicate_ids = len(ids) - len(set(ids))
    split_counts = Counter(case["split"] for case in cases)
    category_counts = Counter(case["failure_category"] for case in cases)
    code_counts = Counter(case["code"] for case in cases)
    sector_counts = Counter(case["sector"] for case in cases)
    rate_counts = Counter(str(case["physical_error_rate"]) for case in cases)
    serial_logical = Counter(str(case["serial_bpgd"]["logical_success"]) for case in cases)
    fast_logical = Counter(str(case["fast_bp"]["logical_success"]) for case in cases)

    strata = defaultdict(lambda: Counter())
    for case in cases:
        key = f'{case["code"]}|{case["sector"]}|p={case["physical_error_rate"]}'
        strata[key][case["failure_category"]] += 1

    problems: list[str] = []
    if duplicate_ids:
        problems.append(f"duplicate case ids: {duplicate_ids}")
    if len(cases) != metadata.get("case_count"):
        problems.append("metadata case_count does not match JSONL rows")
    if not set(split_counts).issubset({"train", "validation", "test"}):
        problems.append("unexpected split label")
    if any(not case.get("syndrome_sha256") for case in cases):
        problems.append("missing syndrome hash")
    if any("physical_error_packed_hex" not in case for case in cases):
        problems.append("missing physical error payload")
    if any("logical_success" not in case["serial_bpgd"] for case in cases):
        problems.append("missing serial logical label")

    analysis = {
        "experiment": "expanded_bb_failure_corpus_analysis_v1",
        "case_count": len(cases),
        "duplicate_case_ids": duplicate_ids,
        "split_counts": dict(split_counts),
        "category_counts": dict(category_counts),
        "code_counts": dict(code_counts),
        "sector_counts": dict(sector_counts),
        "rate_counts": dict(rate_counts),
        "serial_bpgd_logical_success_counts": dict(serial_logical),
        "fast_bp_logical_success_counts": dict(fast_logical),
        "strata": {key: dict(value) for key, value in sorted(strata.items())},
        "validation_passed": not problems,
        "validation_problems": problems,
    }
    (ROOT / "expanded_failure_corpus_analysis.json").write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Expanded Failure Corpus Analysis",
        "",
        f'- Cases: **{len(cases)}**',
        f'- Validation: **{"PASS" if not problems else "FAIL"}**',
        f'- Duplicate IDs: **{duplicate_ids}**',
        "",
        "## Splits",
        "",
    ]
    for key in ("train", "validation", "test"):
        lines.append(f'- {key}: {split_counts.get(key, 0)}')
    lines += ["", "## Failure categories", ""]
    for key, value in category_counts.most_common():
        lines.append(f'- {key}: {value}')
    lines += ["", "## Codes", ""]
    for key, value in sorted(code_counts.items()):
        lines.append(f'- {key}: {value}')
    lines += ["", "## Validation problems", ""]
    if problems:
        lines.extend(f'- {problem}' for problem in problems)
    else:
        lines.append("- None")
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "This is a deliberately enriched hard-case corpus. Its category frequencies must not be interpreted as natural syndrome frequencies or as logical-error-rate estimates.",
    ]
    (ROOT / "EXPANDED_FAILURE_CORPUS_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2, sort_keys=True))

    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
