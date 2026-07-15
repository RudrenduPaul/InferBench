import { describe, it, expect } from "vitest";
import { detectHardware } from "./detect.js";

describe("detectHardware", () => {
  it("returns a profile with the expected shape", () => {
    const profile = detectHardware();
    expect(typeof profile.platform).toBe("string");
    expect(typeof profile.arch).toBe("string");
    expect(profile.totalMemoryGb).toBeGreaterThan(0);
    expect(typeof profile.cpuModel).toBe("string");
    expect(typeof profile.isAppleSilicon).toBe("boolean");
  });

  it("only reports isAppleSilicon true on darwin+arm64", () => {
    const profile = detectHardware();
    if (profile.isAppleSilicon) {
      expect(profile.platform).toBe("darwin");
      expect(profile.arch).toBe("arm64");
    }
  });
});
