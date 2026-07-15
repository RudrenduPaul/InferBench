export class EngineNotFoundError extends Error {
  constructor(public readonly engine: string, binary: string) {
    super(`${engine}: binary "${binary}" not found on PATH -- skipped`);
    this.name = "EngineNotFoundError";
  }
}

export class EngineStartTimeoutError extends Error {
  constructor(public readonly engine: string, timeoutMs: number) {
    super(`${engine}: server did not become ready within ${timeoutMs}ms`);
    this.name = "EngineStartTimeoutError";
  }
}

export class EngineRequestTimeoutError extends Error {
  constructor(public readonly engine: string, timeoutMs: number) {
    super(`${engine}: request timed out after ${timeoutMs}ms`);
    this.name = "EngineRequestTimeoutError";
  }
}

export class BenchmarkParseError extends Error {
  constructor(public readonly engine: string, rawOutput: string) {
    super(`${engine}: could not parse benchmark response`);
    this.name = "BenchmarkParseError";
    this.rawOutput = rawOutput;
  }
  rawOutput: string;
}

export class NoEnginesFoundError extends Error {
  constructor() {
    super(
      "No supported engines found on this machine. Install omlx (brew install omlx) " +
        "or llama.cpp (brew install llama.cpp) and try again.",
    );
    this.name = "NoEnginesFoundError";
  }
}

export class UsageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UsageError";
  }
}
