import type { EngineAdapter } from "../types.js";
import { OmlxAdapter } from "./omlx.js";
import { LlamaCppAdapter } from "./llamacpp.js";
import { UsageError } from "../errors.js";

const ADAPTERS: Record<string, () => EngineAdapter> = {
  omlx: () => new OmlxAdapter(),
  "llama.cpp": () => new LlamaCppAdapter(),
};

export const SUPPORTED_ENGINES = Object.keys(ADAPTERS);

/** Dedupes and validates a user-supplied --engines list. */
export function resolveEngines(names: string[]): EngineAdapter[] {
  const deduped = [...new Set(names)];
  const unknown = deduped.filter((n) => !(n in ADAPTERS));
  if (unknown.length > 0) {
    throw new UsageError(
      `Unknown engine(s): ${unknown.join(", ")}. Supported: ${SUPPORTED_ENGINES.join(", ")}`,
    );
  }
  return deduped.map((n) => ADAPTERS[n]());
}

export function allEngines(): EngineAdapter[] {
  return SUPPORTED_ENGINES.map((n) => ADAPTERS[n]());
}
