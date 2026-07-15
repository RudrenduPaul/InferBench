import { writeFile } from "node:fs/promises";
import type { BenchmarkReport } from "../types.js";

export async function writeJsonReport(
  report: BenchmarkReport,
  filePath: string,
): Promise<void> {
  await writeFile(filePath, JSON.stringify(report, null, 2), "utf-8");
}
