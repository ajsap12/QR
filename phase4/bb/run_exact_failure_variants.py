from __future__ import annotations

"""Replay persisted rare-failure syndromes through semantic variants.

This runner requires `stateful_failure_corpus.json`, containing full syndrome
vectors from the fixed-seed 12,000-shot validation. A SHA-256 digest alone is
not reversible, so the exact corpus must be regenerated and persisted before
this runner can execute the intended 17-case comparison.
"""

import json
from pathlib import Path


REQUIRED_CORPUS = Path(__file__).with_name("stateful_failure_corpus.json")


def main() -> None:
    if not REQUIRED_CORPUS.exists():
        raise FileNotFoundError(
            "Missing stateful_failure_corpus.json. Regenerate the fixed-seed "
            "12,000-shot corpus and persist each full syndrome vector first."
        )
    corpus = json.loads(REQUIRED_CORPUS.read_text(encoding="utf-8"))
    if len(corpus.get("cases", [])) != 17:
        raise ValueError("Expected exactly 17 fixed stateful failure cases")
    raise NotImplementedError(
        "Extended tie/schedule kernel execution begins after corpus validation"
    )


if __name__ == "__main__":
    main()
