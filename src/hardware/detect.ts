import os from "node:os";
import type { HardwareProfile } from "../types.js";

export function detectHardware(): HardwareProfile {
  const platform = os.platform();
  const arch = os.arch();
  const cpus = os.cpus();
  return {
    platform,
    arch,
    totalMemoryGb: Math.round((os.totalmem() / 1024 ** 3) * 10) / 10,
    cpuModel: cpus.length > 0 ? cpus[0].model : "unknown",
    isAppleSilicon: platform === "darwin" && arch === "arm64",
  };
}
