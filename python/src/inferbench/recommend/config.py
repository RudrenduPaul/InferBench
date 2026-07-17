"""
Ported from src/recommend/config.ts.

v0.1 recommendation rule: highest measured average tok/s among engines that
were actually installed and tested. Deliberately simple -- richer
multi-factor scoring (memory, cost) is intentionally deferred until real
usage shows this simple rule picks wrong recommendations.
"""
from __future__ import annotations

from typing import List, Optional

from ..types import EngineBenchmarkResult, Recommendation


def recommend(results: List[EngineBenchmarkResult]) -> Optional[Recommendation]:
    candidates = [r for r in results if r.installed and r.avg_tokens_per_second is not None]
    if not candidates:
        return None

    best = max(candidates, key=lambda r: r.avg_tokens_per_second or 0)

    return Recommendation(
        engine=best.engine,
        reason=(
            f"highest measured throughput on this run ({best.avg_tokens_per_second} tok/s avg) "
            "-- specific to this hardware and model, not a universal ranking"
        ),
    )
