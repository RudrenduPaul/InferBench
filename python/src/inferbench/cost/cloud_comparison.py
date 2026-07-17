"""
Ported from src/cost/cloud_comparison.ts.

Static, versioned pricing snapshot -- not a live API call. Prices drift;
this table is a directional reference, not a real-time quote. Update
PRICING_SNAPSHOT_DATE whenever the numbers below are refreshed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

PRICING_SNAPSHOT_DATE = "2026-07-15"

CLOUD_PRICING_PER_1K_OUTPUT_TOKENS: Dict[str, float] = {
    "claude-5-haiku": 0.0008,
    "claude-5-sonnet": 0.006,
}


@dataclass
class CostComparison:
    cloud_model: str
    cloud_cost_per_1k_tokens_usd: float
    pricing_snapshot_date: str
    note: str


def compare_to_cloud(cloud_model: str) -> Optional[CostComparison]:
    price = CLOUD_PRICING_PER_1K_OUTPUT_TOKENS.get(cloud_model)
    if price is None:
        return None
    return CostComparison(
        cloud_model=cloud_model,
        cloud_cost_per_1k_tokens_usd=price,
        pricing_snapshot_date=PRICING_SNAPSHOT_DATE,
        note=(
            "Local hardware's own amortized cost is not included -- this compares raw "
            "generation cost only. Local inference has $0 marginal per-token cost once "
            "hardware is already owned."
        ),
    )
