import { describe, it, expect } from "vitest";
import { compareToCloud, CLOUD_PRICING_PER_1K_OUTPUT_TOKENS } from "./cloud_comparison.js";

describe("compareToCloud", () => {
  it("returns pricing info for a known model", () => {
    const result = compareToCloud("claude-5-haiku");
    expect(result).not.toBeNull();
    expect(result?.cloudCostPer1kTokensUsd).toBe(
      CLOUD_PRICING_PER_1K_OUTPUT_TOKENS["claude-5-haiku"],
    );
    expect(result?.pricingSnapshotDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("returns null for an unknown model rather than a fabricated price", () => {
    expect(compareToCloud("not-a-real-model")).toBeNull();
  });

  it("discloses that this is not a live quote", () => {
    const result = compareToCloud("claude-5-sonnet");
    expect(result?.note).toMatch(/amortized/i);
  });
});
