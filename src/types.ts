export interface HardwareProfile {
  platform: NodeJS.Platform;
  arch: string;
  totalMemoryGb: number;
  cpuModel: string;
  isAppleSilicon: boolean;
}

export interface EngineAdapter {
  readonly name: string;
  readonly binary: string;
  /** Check whether the engine's binary is installed on this machine. */
  isInstalled(): boolean;
  /**
   * Start the engine's OpenAI-compatible server for the given model spec.
   * Returns the running process and the base URL to send requests to.
   */
  startServer(opts: {
    model: string;
    port: number;
    timeoutMs: number;
    verbose?: boolean;
  }): Promise<StartedServer>;
}

export interface StartedServer {
  process: import("node:child_process").ChildProcess;
  baseUrl: string;
  modelId: string;
  stop(): void;
}

export interface CompletionResult {
  elapsedMs: number;
  completionTokens: number | null;
  cachedPromptTokens: number;
  tokensPerSecond: number | null;
}

export interface PromptRunResult {
  prompt: string;
  ok: boolean;
  error?: string;
  result?: CompletionResult;
}

export interface EngineBenchmarkResult {
  engine: string;
  installed: boolean;
  error?: string;
  runs: PromptRunResult[];
  avgTokensPerSecond: number | null;
  minTokensPerSecond: number | null;
  maxTokensPerSecond: number | null;
}

export interface BenchmarkReport {
  timestamp: string;
  hardware: HardwareProfile;
  model: string;
  engines: EngineBenchmarkResult[];
  recommendation: Recommendation | null;
}

export interface Recommendation {
  engine: string;
  reason: string;
}
