import { writeFile } from "node:fs/promises";
import * as path from "node:path";
import type { BenchmarkReport } from "../types.js";

export class UnsafeOutputPathError extends Error {}

// --out is a plain CLI flag today, but this CLI is also meant to be invoked
// programmatically by agents that may derive the value from less-trusted
// input (a fetched benchmark config, an LLM-generated argument list, etc).
// A relative path containing `..` segments can escape the intended output
// location entirely (`--out ../../../etc/cron.d/x`) -- reject any --out
// value that resolves outside the current working directory. An explicit
// absolute path is still allowed: that's a value the caller typed/passed
// directly, not one that silently escaped via traversal.
function assertSafeOutputPath(filePath: string): void {
  if (path.isAbsolute(filePath)) return;
  const cwd = process.cwd();
  const resolved = path.resolve(cwd, filePath);
  if (resolved !== cwd && !resolved.startsWith(cwd + path.sep)) {
    throw new UnsafeOutputPathError(
      `--out "${filePath}" resolves outside the current working directory (${resolved}). ` +
        "Pass an absolute path if you intend to write outside the working directory.",
    );
  }
}

export async function writeJsonReport(
  report: BenchmarkReport,
  filePath: string,
): Promise<void> {
  assertSafeOutputPath(filePath);
  await writeFile(filePath, JSON.stringify(report, null, 2), "utf-8");
}
