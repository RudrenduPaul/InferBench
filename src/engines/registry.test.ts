import { describe, it, expect } from "vitest";
import { resolveEngines, allEngines, SUPPORTED_ENGINES } from "./registry.js";
import { UsageError } from "../errors.js";

describe("resolveEngines", () => {
  it("dedupes repeated engine names", () => {
    const engines = resolveEngines(["omlx", "omlx", "llama.cpp"]);
    expect(engines).toHaveLength(2);
    expect(engines.map((e) => e.name).sort()).toEqual(["llama.cpp", "omlx"]);
  });

  it("throws UsageError for an unknown engine", () => {
    expect(() => resolveEngines(["not-a-real-engine"])).toThrow(UsageError);
  });

  it("lists the unknown engine name and supported engines in the error", () => {
    try {
      resolveEngines(["bogus"]);
      expect.fail("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(UsageError);
      expect((err as Error).message).toContain("bogus");
      expect((err as Error).message).toContain("omlx");
      expect((err as Error).message).toContain("llama.cpp");
    }
  });
});

describe("allEngines", () => {
  it("returns one adapter per supported engine", () => {
    expect(allEngines()).toHaveLength(SUPPORTED_ENGINES.length);
  });
});
