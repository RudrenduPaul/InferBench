import type {
  EngineAdapter,
  EngineBenchmarkResult,
  PromptRunResult,
} from "./types.js";
import { timedCompletion } from "./harness/measure.js";
import { DEFAULT_PROMPTS, WARMUP_PROMPT } from "./prompts.js";

export interface RunBenchmarkOptions {
  model: string;
  maxTokens?: number;
  serverStartTimeoutMs?: number;
  requestTimeoutMs?: number;
  prompts?: string[];
  verbose?: boolean;
  onProgress?: (line: string) => void;
}

const DEFAULT_MAX_TOKENS = 200;
const DEFAULT_SERVER_START_TIMEOUT_MS = 5 * 60 * 1000;
const DEFAULT_REQUEST_TIMEOUT_MS = 2 * 60 * 1000;

let nextPort = 41000;
function claimPort(): number {
  return nextPort++;
}

/**
 * Benchmarks a single engine. Never throws for an engine-level failure
 * (not installed, server start timeout, request failure) -- per the CEO
 * review's per-engine isolation decision, one bad engine never blocks
 * results from the others. Callers get a result object with installed:false
 * or per-run errors instead.
 */
export async function benchmarkEngine(
  adapter: EngineAdapter,
  opts: RunBenchmarkOptions,
): Promise<EngineBenchmarkResult> {
  const progress = opts.onProgress ?? (() => {});
  const prompts = opts.prompts ?? DEFAULT_PROMPTS;
  const maxTokens = opts.maxTokens ?? DEFAULT_MAX_TOKENS;

  if (!adapter.isInstalled()) {
    progress(`${adapter.name}: not installed, skipped`);
    return {
      engine: adapter.name,
      installed: false,
      error: `binary "${adapter.binary}" not found`,
      runs: [],
      avgTokensPerSecond: null,
      minTokensPerSecond: null,
      maxTokensPerSecond: null,
    };
  }

  progress(`${adapter.name}: starting server...`);
  let server;
  try {
    server = await adapter.startServer({
      model: opts.model,
      port: claimPort(),
      timeoutMs: opts.serverStartTimeoutMs ?? DEFAULT_SERVER_START_TIMEOUT_MS,
      verbose: opts.verbose,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    progress(`${adapter.name}: failed to start (${message})`);
    return {
      engine: adapter.name,
      installed: true,
      error: message,
      runs: [],
      avgTokensPerSecond: null,
      minTokensPerSecond: null,
      maxTokensPerSecond: null,
    };
  }

  try {
    progress(`${adapter.name}: warming up...`);
    try {
      await timedCompletion({
        engine: adapter.name,
        baseUrl: server.baseUrl,
        modelId: server.modelId,
        prompt: WARMUP_PROMPT,
        maxTokens: 16,
        timeoutMs: opts.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      progress(`${adapter.name}: warm-up failed (${message})`);
      return {
        engine: adapter.name,
        installed: true,
        error: `warm-up failed: ${message}`,
        runs: [],
        avgTokensPerSecond: null,
        minTokensPerSecond: null,
        maxTokensPerSecond: null,
      };
    }

    const runs: PromptRunResult[] = [];
    for (let i = 0; i < prompts.length; i++) {
      const prompt = prompts[i];
      progress(`${adapter.name}: [${i + 1}/${prompts.length}] benchmarking...`);
      try {
        const result = await timedCompletion({
          engine: adapter.name,
          baseUrl: server.baseUrl,
          modelId: server.modelId,
          prompt,
          maxTokens,
          timeoutMs: opts.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS,
        });
        runs.push({ prompt, ok: true, result });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        runs.push({ prompt, ok: false, error: message });
      }
    }

    const valid = runs
      .filter((r) => r.ok && r.result?.tokensPerSecond)
      .map((r) => r.result!.tokensPerSecond!);

    return {
      engine: adapter.name,
      installed: true,
      runs,
      avgTokensPerSecond:
        valid.length > 0
          ? Math.round((valid.reduce((a, b) => a + b, 0) / valid.length) * 100) / 100
          : null,
      minTokensPerSecond: valid.length > 0 ? Math.min(...valid) : null,
      maxTokensPerSecond: valid.length > 0 ? Math.max(...valid) : null,
    };
  } finally {
    server.stop();
  }
}
