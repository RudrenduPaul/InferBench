import { spawn } from "node:child_process";
import { EngineStartTimeoutError } from "../errors.js";

export interface SpawnServerOptions {
  /** Engine name, used only for error messages. */
  engine: string;
  /** Executable name or path -- never a shell string. */
  command: string;
  /** Argv array -- never interpolated into a shell string (command injection safety). */
  args: string[];
  /** URL to poll until it responds successfully, indicating the server is ready. */
  readyCheckUrl: string;
  /** Max time to wait for readyCheckUrl to respond before giving up. */
  timeoutMs: number;
  /** Poll interval while waiting for the server to become ready. */
  pollIntervalMs?: number;
  verbose?: boolean;
}

export interface SpawnedServer {
  process: ReturnType<typeof spawn>;
  stop(): void;
}

/**
 * Spawns a long-running server process (never through a shell -- argv array
 * only, to avoid command-injection risk) and polls a URL until it responds,
 * so callers get a server that is actually ready to accept requests rather
 * than racing against startup.
 */
export async function spawnServerAndWaitReady(
  opts: SpawnServerOptions,
): Promise<SpawnedServer> {
  const pollIntervalMs = opts.pollIntervalMs ?? 500;
  const child = spawn(opts.command, opts.args, {
    stdio: opts.verbose ? "inherit" : "ignore",
  });

  const stop = () => {
    if (!child.killed) {
      child.kill();
    }
  };

  const deadline = Date.now() + opts.timeoutMs;
  let lastError: unknown;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(
        `${opts.engine}: process exited early (code ${child.exitCode}) before becoming ready`,
      );
    }
    try {
      const res = await fetch(opts.readyCheckUrl, {
        signal: AbortSignal.timeout(2000),
      });
      if (res.ok) {
        return { process: child, stop };
      }
    } catch (err) {
      lastError = err;
    }
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  stop();
  const timeoutErr = new EngineStartTimeoutError(opts.engine, opts.timeoutMs);
  if (lastError instanceof Error) {
    timeoutErr.cause = lastError;
  }
  throw timeoutErr;
}
