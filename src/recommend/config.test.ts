import { describe, it, expect } from "vitest";
import { recommend } from "./config.js";
import type { EngineBenchmarkResult } from "../types.js";

function fakeResult(
  engine: string,
  installed: boolean,
  avg: number | null,
): EngineBenchmarkResult {
  return {
    engine,
    installed,
    runs: [],
    avgTokensPerSecond: avg,
    minTokensPerSecond: avg,
    maxTokensPerSecond: avg,
  };
}

describe("recommend", () => {
  it("picks the engine with the highest avg tok/s", () => {
    const results = [
      fakeResult("omlx", true, 40),
      fakeResult("llama.cpp", true, 75),
    ];
    const rec = recommend(results);
    expect(rec?.engine).toBe("llama.cpp");
  });

  it("ignores engines that were not installed", () => {
    const results = [
      fakeResult("omlx", false, null),
      fakeResult("llama.cpp", true, 50),
    ];
    const rec = recommend(results);
    expect(rec?.engine).toBe("llama.cpp");
  });

  it("ignores engines with no successful runs (avg null)", () => {
    const results = [
      fakeResult("omlx", true, null),
      fakeResult("llama.cpp", true, 50),
    ];
    const rec = recommend(results);
    expect(rec?.engine).toBe("llama.cpp");
  });

  it("returns null when no engine has a usable result", () => {
    const results = [fakeResult("omlx", false, null), fakeResult("llama.cpp", true, null)];
    expect(recommend(results)).toBeNull();
  });

  it("returns null for an empty result set", () => {
    expect(recommend([])).toBeNull();
  });

  it("states the recommendation is run-specific, not a universal ranking", () => {
    const results = [fakeResult("omlx", true, 60)];
    const rec = recommend(results);
    expect(rec?.reason).toMatch(/this hardware and model/);
    expect(rec?.reason).toMatch(/not a universal ranking/);
  });
});
