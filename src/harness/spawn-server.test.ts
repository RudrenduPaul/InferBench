import { describe, it, expect } from "vitest";
import { spawnServerAndWaitReady } from "./spawn-server.js";
import { EngineStartTimeoutError } from "../errors.js";

/**
 * Regression test for [redacted] Finding 6A: the timeout must be injectable
 * so tests can verify the kill-and-report path in milliseconds, not by
 * actually waiting out a real multi-minute production timeout.
 */
describe("spawnServerAndWaitReady", () => {
  it("throws EngineStartTimeoutError quickly when nothing answers the ready check", async () => {
    const start = Date.now();
    await expect(
      spawnServerAndWaitReady({
        engine: "test-engine",
        command: "sleep",
        args: ["30"], // a harmless long-running process that never opens a port
        readyCheckUrl: "http://127.0.0.1:1/never-listening", // port 1 -- nothing listens here
        timeoutMs: 300,
        pollIntervalMs: 50,
      }),
    ).rejects.toThrow(EngineStartTimeoutError);
    const elapsed = Date.now() - start;
    // Should resolve close to the 300ms timeout, not hang for the real
    // 5-minute production default.
    expect(elapsed).toBeLessThan(2000);
  });

  it("throws immediately if the process exits before becoming ready", async () => {
    await expect(
      spawnServerAndWaitReady({
        engine: "test-engine",
        command: "false", // exits immediately with a non-zero code
        args: [],
        readyCheckUrl: "http://127.0.0.1:1/never-listening",
        timeoutMs: 5000,
        pollIntervalMs: 50,
      }),
    ).rejects.toThrow(/exited early/);
  });
});
