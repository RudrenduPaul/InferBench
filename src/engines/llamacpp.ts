import { execFileSync } from "node:child_process";
import type { EngineAdapter, StartedServer } from "../types.js";
import { spawnServerAndWaitReady } from "../harness/spawn-server.js";
import { EngineNotFoundError, UsageError } from "../errors.js";

const BINARY = "llama-server";

export class LlamaCppAdapter implements EngineAdapter {
  readonly name = "llama.cpp";
  readonly binary = BINARY;

  isInstalled(): boolean {
    try {
      execFileSync(BINARY, ["--version"], { stdio: "ignore" });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * `model` is treated as a Hugging Face repo spec (e.g.
   * "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M") -- llama.cpp's own
   * -hf flag downloads and caches it automatically, no manual step needed.
   */
  async startServer(opts: {
    model: string;
    port: number;
    timeoutMs: number;
    verbose?: boolean;
  }): Promise<StartedServer> {
    if (!this.isInstalled()) {
      throw new EngineNotFoundError(this.name, BINARY);
    }
    if (opts.model.startsWith("-")) {
      throw new UsageError(
        `Invalid --model value "${opts.model}": cannot start with "-" (would be parsed as a flag by llama-server, not a model spec)`,
      );
    }
    const spawned = await spawnServerAndWaitReady({
      engine: this.name,
      command: BINARY,
      args: [
        "-hf",
        opts.model,
        "--port",
        String(opts.port),
        "--host",
        "127.0.0.1",
      ],
      readyCheckUrl: `http://127.0.0.1:${opts.port}/v1/models`,
      timeoutMs: opts.timeoutMs,
      verbose: opts.verbose,
    });
    return {
      process: spawned.process,
      baseUrl: `http://127.0.0.1:${opts.port}`,
      modelId: "default",
      stop: spawned.stop,
    };
  }
}
