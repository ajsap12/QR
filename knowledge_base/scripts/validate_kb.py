from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sources.jsonl"
VALID_SOURCE_TYPES = {
    "paper", "preprint", "conference", "repository", "patent",
    "industry_report", "technical_blog", "dataset", "standard",
}
VALID_TAGS = {"FACT", "PUB", "PAT", "REPO", "ENG", "MARKET", "HYP", "SPEC"}
REQUIRED = {
    "id", "title", "source_type", "publication_date", "evidence_tags",
    "categories", "main_contribution", "limitations", "relevance_to_qr",
    "extraction_confidence", "review_status",
}


def validate_record(record: dict, line_number: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - set(record))
    if missing:
        errors.append(f"line {line_number}: missing fields {missing}")
    if record.get("source_type") not in VALID_SOURCE_TYPES:
        errors.append(f"line {line_number}: invalid source_type {record.get('source_type')!r}")
    tags = set(record.get("evidence_tags", []))
    if not tags or not tags.issubset(VALID_TAGS):
        errors.append(f"line {line_number}: invalid evidence_tags {sorted(tags)}")
    confidence = record.get("extraction_confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append(f"line {line_number}: extraction_confidence must be between 0 and 1")
    if record.get("review_status") not in {"seed", "screened", "verified", "rejected"}:
        errors.append(f"line {line_number}: invalid review_status")
    if not isinstance(record.get("categories"), list) or not record.get("categories"):
        errors.append(f"line {line_number}: categories must be a non-empty list")
    return errors


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Missing {DATA}")

    records: list[dict] = []
    errors: list[str] = []
    for line_number, raw in enumerate(DATA.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc}")
            continue
        errors.extend(validate_record(record, line_number))
        records.append(record)

    ids = [record.get("id") for record in records]
    duplicates = [key for key, count in Counter(ids).items() if key is not None and count > 1]
    if duplicates:
        errors.append(f"duplicate ids: {duplicates}")

    summary = {
        "record_count": len(records),
        "source_type_counts": dict(Counter(record.get("source_type") for record in records)),
        "review_status_counts": dict(Counter(record.get("review_status") for record in records)),
        "category_counts": dict(Counter(category for record in records for category in record.get("categories", []))),
        "validation_passed": not errors,
        "errors": errors,
    }
    output = ROOT / "reports" / "validation_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
