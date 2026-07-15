#!/usr/bin/env node
import { Command } from "commander";
import { detectHardware } from "./hardware/detect.js";
import { resolveEngines, allEngines, SUPPORTED_ENGINES } from "./engines/registry.js";
import { benchmarkEngine } from "./benchmark.js";
import { recommend } from "./recommend/config.js";
import { writeJsonReport } from "./report/json.js";
import { NoEnginesFoundError, UsageError } from "./errors.js";
import type { BenchmarkReport } from "./types.js";

const program = new Command();

program
  .name("inferbench")
  .description(
    "Benchmarks local-LLM-inference engines (omlx, llama.cpp) on your own hardware, live.",
  )
  .version("0.1.0");

program
  .command("run")
  .description("Benchmark installed engines against a model")
  .requiredOption("--model <spec>", "Model spec (engine-specific, see README)")
  .option(
    "--engines <list>",
    `Comma-separated engines to test (default: all supported -- ${SUPPORTED_ENGINES.join(", ")})`,
  )
  .option("--max-tokens <n>", "Max completion tokens per prompt", "200")
  .option("--json", "Output machine-readable JSON instead of a human table")
  .option("--out <file>", "Also write the full JSON report to this file")
  .option("--verbose", "Show raw engine server stdout/stderr")
  .action(async (options) => {
    try {
      await runCommand(options);
    } catch (err) {
      if (err instanceof UsageError || err instanceof NoEnginesFoundError) {
        console.error(err.message);
        process.exit(1);
      }
      throw err;
    }
  });

async function runCommand(options: {
  model: string;
  engines?: string;
  maxTokens: string;
  json?: boolean;
  out?: string;
  verbose?: boolean;
}): Promise<void> {
  const adapters = options.engines
    ? resolveEngines(options.engines.split(","))
    : allEngines();

  const hardware = detectHardware();
  if (!options.json) {
    console.log(
      `Hardware: ${hardware.cpuModel} (${hardware.platform}/${hardware.arch}), ${hardware.totalMemoryGb}GB\n`,
    );
  }

  const results = [];
  for (const adapter of adapters) {
    const result = await benchmarkEngine(adapter, {
      model: options.model,
      maxTokens: Number(options.maxTokens),
      verbose: options.verbose,
      onProgress: options.json ? undefined : (line) => console.log(line),
    });
    results.push(result);
  }

  const testedAny = results.some((r) => r.installed);
  if (!testedAny) {
    throw new NoEnginesFoundError();
  }

  const report: BenchmarkReport = {
    timestamp: new Date().toISOString(),
    hardware,
    model: options.model,
    engines: results,
    recommendation: recommend(results),
  };

  if (options.out) {
    await writeJsonReport(report, options.out);
  }

  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
    return;
  }

  console.log("\nResults:");
  for (const r of results) {
    if (!r.installed) {
      console.log(`  ${r.engine}: not installed, skipped`);
      continue;
    }
    if (r.avgTokensPerSecond === null) {
      console.log(`  ${r.engine}: FAILED (${r.error ?? "no successful runs"})`);
      continue;
    }
    console.log(
      `  ${r.engine}: avg ${r.avgTokensPerSecond} tok/s (range ${r.minTokensPerSecond}-${r.maxTokensPerSecond}, n=${r.runs.filter((x) => x.ok).length})`,
    );
  }

  if (report.recommendation) {
    console.log(`\nRecommendation: ${report.recommendation.engine} -- ${report.recommendation.reason}`);
  }

  if (options.out) {
    console.log(`\nFull report: ${options.out}`);
  }
}

program.parseAsync(process.argv);
