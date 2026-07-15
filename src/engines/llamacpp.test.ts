import { describe, it, expect, vi, beforeEach } from "vitest";
import { EngineNotFoundError } from "../errors.js";

const execFileSyncMock = vi.fn();
vi.mock("node:child_process", () => ({
  execFileSync: (...args: unknown[]) => execFileSyncMock(...args),
}));

describe("LlamaCppAdapter", () => {
  beforeEach(() => {
    execFileSyncMock.mockReset();
  });

  it("isInstalled() returns true when the binary check succeeds", async () => {
    execFileSyncMock.mockReturnValue(Buffer.from(""));
    const { LlamaCppAdapter } = await import("./llamacpp.js");
    const adapter = new LlamaCppAdapter();
    expect(adapter.isInstalled()).toBe(true);
    expect(execFileSyncMock).toHaveBeenCalledWith(
      "llama-server",
      ["--version"],
      expect.anything(),
    );
  });

  it("isInstalled() returns false when the binary check throws", async () => {
    execFileSyncMock.mockImplementation(() => {
      throw new Error("command not found");
    });
    const { LlamaCppAdapter } = await import("./llamacpp.js");
    const adapter = new LlamaCppAdapter();
    expect(adapter.isInstalled()).toBe(false);
  });

  it("startServer throws EngineNotFoundError when the binary is missing", async () => {
    execFileSyncMock.mockImplementation(() => {
      throw new Error("command not found");
    });
    const { LlamaCppAdapter } = await import("./llamacpp.js");
    const adapter = new LlamaCppAdapter();
    await expect(
      adapter.startServer({ model: "foo", port: 9999, timeoutMs: 100 }),
    ).rejects.toThrow(EngineNotFoundError);
  });
});
