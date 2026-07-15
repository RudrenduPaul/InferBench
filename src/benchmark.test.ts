import { describe, it, expect, vi, afterEach } from "vitest";
import { benchmarkEngine } from "./benchmark.js";
import type { EngineAdapter } from "./types.js";

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetchWithTokenCounts(tokenCounts: number[]) {
  let call = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async () => {
      const tokens = tokenCounts[Math.min(call, tokenCounts.length - 1)];
      call++;
      return {
        ok: true,
        text: () =>
          Promise.resolve(
            JSON.stringify({
              usage: { completion_tokens: tokens, prompt_tokens_details: { cached_tokens: 0 } },
            }),
          ),
      };
    }),
  );
}

function makeWorkingAdapter(name: string): EngineAdapter {
  const stop = vi.fn();
  return {
    name,
    binary: `${name}-binary`,
    isInstalled: () => true,
    startServer: vi.fn().mockResolvedValue({
      process: {} as never,
      baseUrl: "http://fake",
      modelId: "test-model",
      stop,
    }),
  };
}

function makeUninstalledAdapter(name: string): EngineAdapter {
  return {
    name,
    binary: `${name}-binary`,
    isInstalled: () => false,
    startServer: vi.fn(),
  };
}

function makeFailingStartAdapter(name: string, error: Error): EngineAdapter {
  return {
    name,
    binary: `${name}-binary`,
    isInstalled: () => true,
    startServer: vi.fn().mockRejectedValue(error),
  };
}

describe("benchmarkEngine", () => {
  it("reports installed:false and never throws when the binary is missing", async () => {
    const adapter = makeUninstalledAdapter("phantom-engine");
    const result = await benchmarkEngine(adapter, { model: "any" });
    expect(result.installed).toBe(false);
    expect(result.avgTokensPerSecond).toBeNull();
    expect(result.runs).toHaveLength(0);
  });

  it("reports a failure result instead of throwing when the server fails to start", async () => {
    const adapter = makeFailingStartAdapter(
      "broken-engine",
      new Error("could not bind port"),
    );
    const result = await benchmarkEngine(adapter, { model: "any" });
    expect(result.installed).toBe(true);
    expect(result.error).toContain("could not bind port");
    expect(result.avgTokensPerSecond).toBeNull();
  });

  it("calls onProgress with per-engine status lines", async () => {
    const adapter = makeUninstalledAdapter("progress-engine");
    const lines: string[] = [];
    await benchmarkEngine(adapter, { model: "any", onProgress: (l) => lines.push(l) });
    expect(lines.some((l) => l.includes("not installed"))).toBe(true);
  });

  it("runs the warm-up call plus the full prompt set and aggregates real tok/s", async () => {
    // 8 prompt runs + 1 warm-up = 9 fetch calls; token counts chosen so
    // avg/min/max are all distinct and easy to assert on.
    stubFetchWithTokenCounts([5, 10, 20, 30, 15, 25, 35, 5, 40]);
    const adapter = makeWorkingAdapter("fake-engine");
    const progressLines: string[] = [];

    const result = await benchmarkEngine(adapter, {
      model: "test-model",
      prompts: ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"],
      onProgress: (l) => progressLines.push(l),
    });

    expect(result.installed).toBe(true);
    expect(result.runs).toHaveLength(8);
    expect(result.runs.every((r) => r.ok)).toBe(true);
    expect(result.avgTokensPerSecond).toBeGreaterThan(0);
    expect(result.minTokensPerSecond).toBeLessThanOrEqual(result.maxTokensPerSecond!);
    expect(progressLines.some((l) => l.includes("warming up"))).toBe(true);
    expect(progressLines.some((l) => l.includes("[8/8]"))).toBe(true);
  });

  it("stops the server even if a prompt run fails mid-sweep", async () => {
    const stop = vi.fn();
    const adapter: EngineAdapter = {
      name: "flaky-engine",
      binary: "flaky-binary",
      isInstalled: () => true,
      startServer: vi.fn().mockResolvedValue({
        process: {} as never,
        baseUrl: "http://fake",
        modelId: "test-model",
        stop,
      }),
    };
    let call = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async () => {
        call++;
        if (call === 2) throw new Error("connection reset");
        return {
          ok: true,
          text: () =>
            Promise.resolve(JSON.stringify({ usage: { completion_tokens: 10 } })),
        };
      }),
    );

    const result = await benchmarkEngine(adapter, {
      model: "test-model",
      prompts: ["p1"],
    });

    expect(result.runs[0].ok).toBe(false);
    expect(result.runs[0].error).toContain("connection reset");
    expect(stop).toHaveBeenCalled();
  });

  it("reports a failure result when the warm-up call itself fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("warm-up connection refused")),
    );
    const adapter = makeWorkingAdapter("cold-engine");
    const result = await benchmarkEngine(adapter, { model: "test-model" });
    expect(result.error).toContain("warm-up failed");
    expect(result.avgTokensPerSecond).toBeNull();
  });

  it("never lets one adapter's failure affect a second adapter's own result object", async () => {
    // Per [redacted] Finding 2A: per-engine isolation. Simulated here at the
    // unit level -- the CLI loop (src/cli.ts) calls benchmarkEngine once per
    // adapter and collects results independently, so a failing adapter
    // simply produces its own failed result without throwing.
    const broken = makeFailingStartAdapter("broken", new Error("boom"));
    const missing = makeUninstalledAdapter("missing");

    const results = await Promise.all([
      benchmarkEngine(broken, { model: "any" }),
      benchmarkEngine(missing, { model: "any" }),
    ]);

    expect(results[0].error).toContain("boom");
    expect(results[1].installed).toBe(false);
  });
});
