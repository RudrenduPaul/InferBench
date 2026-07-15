import { describe, it, expect, vi, afterEach } from "vitest";
import { timedCompletion } from "./measure.js";
import { BenchmarkParseError, EngineRequestTimeoutError } from "../errors.js";

afterEach(() => {
  vi.unstubAllGlobals();
});

/**
 * Regression test for a real bug caught during a live end-to-end run:
 * fetch() resolves as soon as HTTP headers arrive, not when the full
 * response body (and therefore generation) is done. Measuring elapsed
 * time right after `await fetch(...)` produced a physically impossible
 * 64,646 tok/s against a real omlx server. This test simulates that same
 * gap -- a fast header response, then a slow body read -- and asserts the
 * measured elapsed time reflects the SLOW total, not the fast header time.
 */
describe("timedCompletion", () => {
  it("measures elapsed time across the full response body, not just headers", async () => {
    const fakeResponse = {
      ok: true,
      text: () =>
        new Promise<string>((resolve) => {
          setTimeout(() => {
            resolve(
              JSON.stringify({
                usage: {
                  completion_tokens: 10,
                  prompt_tokens_details: { cached_tokens: 0 },
                },
              }),
            );
          }, 100); // simulates the slow body-read/generation phase
        }),
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(fakeResponse), // fetch() itself resolves "instantly"
    );

    const result = await timedCompletion({
      engine: "test-engine",
      baseUrl: "http://fake",
      modelId: "test-model",
      prompt: "hi",
      maxTokens: 16,
      timeoutMs: 5000,
    });

    // If this ever regresses to measuring only fetch()'s resolution time,
    // elapsedMs would be ~0-5ms and tokensPerSecond would blow up into the
    // thousands, exactly like the real bug.
    expect(result.elapsedMs).toBeGreaterThanOrEqual(90);
    expect(result.completionTokens).toBe(10);
    expect(result.tokensPerSecond).not.toBeNull();
    expect(result.tokensPerSecond!).toBeLessThan(200);
  });

  it("parses cachedPromptTokens when present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: () =>
          Promise.resolve(
            JSON.stringify({
              usage: {
                completion_tokens: 5,
                prompt_tokens_details: { cached_tokens: 39 },
              },
            }),
          ),
      }),
    );
    const result = await timedCompletion({
      engine: "test-engine",
      baseUrl: "http://fake",
      modelId: "test-model",
      prompt: "hi",
      maxTokens: 16,
      timeoutMs: 5000,
    });
    expect(result.cachedPromptTokens).toBe(39);
  });

  it("defaults cachedPromptTokens to 0 when absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ usage: { completion_tokens: 5 } })),
      }),
    );
    const result = await timedCompletion({
      engine: "test-engine",
      baseUrl: "http://fake",
      modelId: "test-model",
      prompt: "hi",
      maxTokens: 16,
      timeoutMs: 5000,
    });
    expect(result.cachedPromptTokens).toBe(0);
  });

  it("throws BenchmarkParseError on malformed JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: () => Promise.resolve("not json"),
      }),
    );
    await expect(
      timedCompletion({
        engine: "test-engine",
        baseUrl: "http://fake",
        modelId: "test-model",
        prompt: "hi",
        maxTokens: 16,
        timeoutMs: 5000,
      }),
    ).rejects.toThrow(BenchmarkParseError);
  });

  it("throws BenchmarkParseError on a non-ok HTTP response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: () => Promise.resolve("internal error"),
      }),
    );
    await expect(
      timedCompletion({
        engine: "test-engine",
        baseUrl: "http://fake",
        modelId: "test-model",
        prompt: "hi",
        maxTokens: 16,
        timeoutMs: 5000,
      }),
    ).rejects.toThrow(BenchmarkParseError);
  });

  it("throws EngineRequestTimeoutError when fetch aborts with a TimeoutError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(Object.assign(new Error("timed out"), { name: "TimeoutError" })),
    );
    await expect(
      timedCompletion({
        engine: "test-engine",
        baseUrl: "http://fake",
        modelId: "test-model",
        prompt: "hi",
        maxTokens: 16,
        timeoutMs: 50,
      }),
    ).rejects.toThrow(EngineRequestTimeoutError);
  });

  it("returns null tokensPerSecond when completion_tokens is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ usage: {} })),
      }),
    );
    const result = await timedCompletion({
      engine: "test-engine",
      baseUrl: "http://fake",
      modelId: "test-model",
      prompt: "hi",
      maxTokens: 16,
      timeoutMs: 5000,
    });
    expect(result.completionTokens).toBeNull();
    expect(result.tokensPerSecond).toBeNull();
  });
});
