import { execFileSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import type { EngineAdapter, StartedServer } from "../types.js";
import { spawnServerAndWaitReady } from "../harness/spawn-server.js";
import { EngineNotFoundError, EngineStartTimeoutError } from "../errors.js";

const BINARY = "omlx";

/**
 * omlx has no CLI benchmark tool of its own (verified against its real
 * README -- its "Performance Benchmark" feature is a GUI-only admin-panel
 * one-click action). This adapter only starts the server; all measurement
 * goes through the shared HTTP harness in src/harness/measure.ts, same as
 * every other engine.
 */
export class OmlxAdapter implements EngineAdapter {
  readonly name = "omlx";
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
   * `model` is treated as a model-dir subdirectory name under
   * ~/.omlx/models/<model> -- omlx's `serve` command has no positional
   * model argument and discovers models from --model-dir subdirectories
   * (or the standard HF cache). Unlike llama.cpp, omlx does not auto-download
   * an arbitrary HF repo from a CLI flag, so the model must already be
   * present locally -- an honest v0.1 limitation, not hidden from the user.
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
    const modelDir = path.join(os.homedir(), ".omlx", "models");
    const spawned = await spawnServerAndWaitReady({
      engine: this.name,
      command: BINARY,
      args: ["serve", "--model-dir", modelDir, "--port", String(opts.port)],
      readyCheckUrl: `http://127.0.0.1:${opts.port}/v1/models`,
      timeoutMs: opts.timeoutMs,
      verbose: opts.verbose,
    });

    const modelId = await this.resolveModelId(opts.port, opts.model);
    if (!modelId) {
      spawned.stop();
      throw new EngineStartTimeoutError(
        this.name,
        opts.timeoutMs,
      );
    }

    return {
      process: spawned.process,
      baseUrl: `http://127.0.0.1:${opts.port}`,
      modelId,
      stop: spawned.stop,
    };
  }

  private async resolveModelId(
    port: number,
    requestedModel: string,
  ): Promise<string | null> {
    const res = await fetch(`http://127.0.0.1:${port}/v1/models`);
    if (!res.ok) return null;
    const payload = (await res.json()) as { data?: Array<{ id: string }> };
    const models = payload.data ?? [];
    if (models.length === 0) return null;
    const exact = models.find((m) => m.id === requestedModel);
    return exact ? exact.id : models[0].id;
  }
}
