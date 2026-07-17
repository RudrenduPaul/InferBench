#!/usr/bin/env python3
"""
Using InferBench as a performance-floor gate: run a benchmark, and fail
(non-zero exit) if the best measured throughput falls below a minimum
acceptable tok/s -- useful for a scheduled job on a fixed self-hosted
runner tracking whether an engine/driver upgrade regressed throughput
(see docs/integrations/ci.md for why this is deliberately NOT recommended
as a per-PR gate: it needs a real model download and stable hardware).

Usage:
    python3 gate.py <model-spec> <min-tok-s>

Example:
    python3 gate.py qwen2.5-1.5b-instruct-4bit 20
"""
from __future__ import annotations

import sys

from inferbench import all_engines, benchmark_engine, recommend


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <model-spec> <min-tok-s>", file=sys.stderr)
        return 2

    model = sys.argv[1]
    try:
        min_tokens_per_second = float(sys.argv[2])
    except ValueError:
        print(f"<min-tok-s> must be a number, got {sys.argv[2]!r}", file=sys.stderr)
        return 2

    results = [benchmark_engine(adapter, model=model) for adapter in all_engines()]
    best = recommend(results)

    if best is None:
        print("GATE FAILED: no engine produced a usable benchmark result.")
        return 1

    best_result = next(r for r in results if r.engine == best.engine)
    measured = best_result.avg_tokens_per_second or 0.0

    if measured < min_tokens_per_second:
        print(
            f"GATE FAILED: best engine ({best.engine}) measured {measured} tok/s, "
            f"below the required {min_tokens_per_second} tok/s floor."
        )
        return 1

    print(f"GATE PASSED: {best.engine} measured {measured} tok/s (floor: {min_tokens_per_second}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
