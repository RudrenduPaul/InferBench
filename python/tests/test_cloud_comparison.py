from __future__ import annotations

import re

from inferbench.cost.cloud_comparison import CLOUD_PRICING_PER_1K_OUTPUT_TOKENS, compare_to_cloud


def test_returns_pricing_info_for_a_known_model():
    result = compare_to_cloud("claude-5-haiku")
    assert result is not None
    assert result.cloud_cost_per_1k_tokens_usd == CLOUD_PRICING_PER_1K_OUTPUT_TOKENS["claude-5-haiku"]
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", result.pricing_snapshot_date)


def test_returns_none_for_an_unknown_model_rather_than_a_fabricated_price():
    assert compare_to_cloud("not-a-real-model") is None


def test_discloses_that_this_is_not_a_live_quote():
    result = compare_to_cloud("claude-5-sonnet")
    assert result is not None
    assert "amortized" in result.note.lower()
