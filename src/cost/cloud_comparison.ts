/**
 * Static, versioned pricing snapshot -- not a live API call. Prices drift;
 * this table is a directional reference, not a real-time quote. Update the
 * date below whenever prices are refreshed.
 */
export const PRICING_SNAPSHOT_DATE = "2026-07-15";

export const CLOUD_PRICING_PER_1K_OUTPUT_TOKENS: Record<string, number> = {
  "claude-5-haiku": 0.0008,
  "claude-5-sonnet": 0.006,
};

export interface CostComparison {
  cloudModel: string;
  cloudCostPer1kTokensUsd: number;
  pricingSnapshotDate: string;
  note: string;
}

export function compareToCloud(cloudModel: string): CostComparison | null {
  const price = CLOUD_PRICING_PER_1K_OUTPUT_TOKENS[cloudModel];
  if (price === undefined) return null;
  return {
    cloudModel,
    cloudCostPer1kTokensUsd: price,
    pricingSnapshotDate: PRICING_SNAPSHOT_DATE,
    note:
      "Local hardware's own amortized cost is not included -- this compares raw " +
      "generation cost only. Local inference has $0 marginal per-token cost once " +
      "hardware is already owned.",
  };
}
