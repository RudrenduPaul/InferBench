import type { EngineBenchmarkResult, Recommendation } from "../types.js";

/**
 * v0.1 recommendation rule: highest measured average tok/s among engines
 * that were actually installed and tested. Deliberately simple -- richer
 * multi-factor scoring (memory, cost) is intentionally deferred until real
 * usage shows this simple rule picks wrong recommendations.
 */
export function recommend(results: EngineBenchmarkResult[]): Recommendation | null {
  const candidates = results.filter(
    (r) => r.installed && r.avgTokensPerSecond !== null,
  );
  if (candidates.length === 0) return null;

  const best = candidates.reduce((a, b) =>
    (b.avgTokensPerSecond ?? 0) > (a.avgTokensPerSecond ?? 0) ? b : a,
  );

  return {
    engine: best.engine,
    reason: `highest measured throughput on this run (${best.avgTokensPerSecond} tok/s avg) -- specific to this hardware and model, not a universal ranking`,
  };
}
