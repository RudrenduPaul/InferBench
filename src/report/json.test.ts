import { describe, it, expect, afterEach } from "vitest";
import { mkdtempSync, mkdirSync, rmSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { writeJsonReport, UnsafeOutputPathError } from "./json.js";
import type { BenchmarkReport } from "../types.js";

const REPORT: BenchmarkReport = {
  timestamp: "2026-07-18T00:00:00.000Z",
  hardware: {
    platform: "linux",
    arch: "x64",
    totalMemoryGb: 32,
    cpuModel: "Test CPU",
    isAppleSilicon: false,
  },
  model: "test-model",
  engines: [],
  recommendation: null,
};

describe("writeJsonReport", () => {
  let tmpDir: string;
  let originalCwd: string;

  afterEach(() => {
    if (originalCwd) process.chdir(originalCwd);
    if (tmpDir) rmSync(tmpDir, { recursive: true, force: true });
  });

  it("writes the report to a plain relative path within the working directory", async () => {
    tmpDir = mkdtempSync(path.join(tmpdir(), "inferbench-report-"));
    originalCwd = process.cwd();
    process.chdir(tmpDir);

    await writeJsonReport(REPORT, "report.json");

    const written = JSON.parse(readFileSync(path.join(tmpDir, "report.json"), "utf-8"));
    expect(written.model).toBe("test-model");
  });

  it("writes the report to a nested relative path within the working directory", async () => {
    tmpDir = mkdtempSync(path.join(tmpdir(), "inferbench-report-"));
    originalCwd = process.cwd();
    process.chdir(tmpDir);

    // fs/promises.writeFile requires the parent directory to already exist,
    // same as the pre-fix behavior -- this test isn't exercising directory
    // creation, just that a nested-but-contained path is accepted.
    mkdirSync(path.join(tmpDir, "out"));
    await writeJsonReport(REPORT, path.join("out", "report.json"));

    expect(existsSync(path.join(tmpDir, "out", "report.json"))).toBe(true);
  });

  it("rejects a relative --out path that traverses outside the working directory", async () => {
    tmpDir = mkdtempSync(path.join(tmpdir(), "inferbench-report-"));
    originalCwd = process.cwd();
    process.chdir(tmpDir);

    await expect(
      writeJsonReport(REPORT, path.join("..", "..", "outside-report.json")),
    ).rejects.toThrow(UnsafeOutputPathError);
  });

  it("allows an explicit absolute --out path outside the working directory", async () => {
    tmpDir = mkdtempSync(path.join(tmpdir(), "inferbench-report-"));
    originalCwd = process.cwd();
    process.chdir(tmpDir);

    const outsideDir = mkdtempSync(path.join(tmpdir(), "inferbench-report-outside-"));
    const absoluteOut = path.join(outsideDir, "report.json");
    try {
      await writeJsonReport(REPORT, absoluteOut);
      expect(existsSync(absoluteOut)).toBe(true);
    } finally {
      rmSync(outsideDir, { recursive: true, force: true });
    }
  });
});
