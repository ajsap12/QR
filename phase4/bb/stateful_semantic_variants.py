from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

from stateful_sum_product_numba import build_tanner_graph, decode_stateful_sum_product

TieBreak = Literal["lowest_index", "highest_index", "seeded_random"]


@dataclass(frozen=True)
class SemanticVariant:
    name: str
    iterations_per_round: int = 100
    numeric_clip: float = 50.0
    tie_break: TieBreak = "lowest_index"


SUPPORTED_VARIANTS = (
    SemanticVariant("baseline_parallel_lowest_index"),
    SemanticVariant("parallel_highest_index", tie_break="highest_index"),
    SemanticVariant("parallel_seeded_random_ties", tie_break="seeded_random"),
    SemanticVariant("parallel_clip_25", numeric_clip=25.0),
    SemanticVariant("parallel_clip_100", numeric_clip=100.0),
    SemanticVariant("parallel_T_50", iterations_per_round=50),
    SemanticVariant("parallel_T_200", iterations_per_round=200),
)


def decode_baseline_variant(
    parity_check: Sequence[Sequence[int]],
    syndrome: Sequence[int],
    error_rate: float,
    variant: SemanticVariant,
):
    """Run variants already supported by the optimized baseline engine.

    The current optimized kernel directly supports T and clipping. Alternate tie
    policies require the extended kernel in `run_exact_failure_variants.py`; this
    helper deliberately rejects them rather than silently pretending support.
    """
    if variant.tie_break != "lowest_index":
        raise NotImplementedError(
            "Alternate tie policies require the extended diagnostic kernel"
        )
    graph = build_tanner_graph(parity_check)
    return decode_stateful_sum_product(
        graph.h,
        graph.check_edges,
        graph.check_degrees,
        graph.edge_variables,
        graph.variable_edges,
        graph.variable_degrees,
        np.asarray(syndrome, dtype=np.uint8),
        error_rate,
        variant.iterations_per_round,
        25.0,
        variant.numeric_clip,
    )
