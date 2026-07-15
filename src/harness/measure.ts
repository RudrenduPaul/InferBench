import { EngineRequestTimeoutError, BenchmarkParseError } from "../errors.js";
import type { CompletionResult } from "../types.js";

export interface TimedCompletionOptions {
  engine: string;
  baseUrl: string;
  modelId: string;
  prompt: string;
  maxTokens: number;
  timeoutMs: number;
}

/**
 * Sends one timed chat-completion request to an engine's OpenAI-compatible
 * server and measures wall-clock time + reported token counts. This is the
 * ONE shared measurement code path for every engine -- the architecture
 * decision that replaced per-engine benchmark-CLI parsing (omlx has no CLI
 * benchmark tool at all; this makes the comparison genuinely apples-to-apples
 * since the same code measures every engine).
 */
export async function timedCompletion(
  opts: TimedCompletionOptions,
): Promise<CompletionResult> {
  const body = JSON.stringify({
    model: opts.modelId,
    messages: [{ role: "user", content: opts.prompt }],
    max_tokens: opts.maxTokens,
    stream: false,
  });

  // Elapsed time must be measured across the FULL request, including
  // reading the response body -- fetch() itself resolves as soon as
  // headers arrive, before generation is done streaming back. Measuring
  // right after `await fetch(...)` (a real bug caught during a live
  // end-to-end run: it produced a physically impossible 64,646 tok/s)
  // only captures time-to-first-byte, not actual generation time.
  const start = performance.now();
  let response: Response;
  try {
    response = await fetch(`${opts.baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: AbortSignal.timeout(opts.timeoutMs),
    });
  } catch (err) {
    if (err instanceof Error && err.name === "TimeoutError") {
      throw new EngineRequestTimeoutError(opts.engine, opts.timeoutMs);
    }
    throw err;
  }

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "");
    throw new BenchmarkParseError(opts.engine, `HTTP ${response.status}: ${errorBody}`);
  }

  let payload: unknown;
  const rawText = await response.text();
  const elapsedMs = performance.now() - start;
  try {
    payload = JSON.parse(rawText);
  } catch {
    throw new BenchmarkParseError(opts.engine, rawText);
  }

  const usage = (payload as Record<string, unknown>)?.usage as
    | Record<string, unknown>
    | undefined;
  const completionTokens =
    typeof usage?.completion_tokens === "number" ? usage.completion_tokens : null;
  const promptTokensDetails = usage?.prompt_tokens_details as
    | Record<string, unknown>
    | undefined;
  const cachedPromptTokens =
    typeof promptTokensDetails?.cached_tokens === "number"
      ? promptTokensDetails.cached_tokens
      : 0;

  const tokensPerSecond =
    completionTokens && elapsedMs > 0
      ? completionTokens / (elapsedMs / 1000)
      : null;

  return {
    elapsedMs: Math.round(elapsedMs),
    completionTokens,
    cachedPromptTokens,
    tokensPerSecond: tokensPerSecond ? Math.round(tokensPerSecond * 100) / 100 : null,
  };
}
