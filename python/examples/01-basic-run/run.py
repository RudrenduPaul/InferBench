#!/usr/bin/env python3
"""
The core library call: detect_hardware() + benchmark_engine() for every
installed engine, printed as a human-readable summary. This is what
`inferbench run` itself calls internally -- the CLI (inferbench/cli.py) is
a thin wrapper over the same functions used here directly.

Usage:
    python3 run.py <model-spec>

Example:
    python3 run.py qwen2.5-1.5b-instruct-4bit   # omlx model-dir name
    python3 run.py "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"  # llama.cpp HF spec

If no supported engine is installed, this prints that plainly instead of
crashing -- see the `installed` field each result carries.
"""
from __future__ import annotations

import sys

from inferbench import all_engines, benchmark_engine, detect_hardware, recommend


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <model-spec>", file=sys.stderr)
        return 2

    model = sys.argv[1]
    hardware = detect_hardware()
    print(f"Hardware: {hardware.cpu_model} ({hardware.platform}/{hardware.arch}), {hardware.total_memory_gb}GB\n")

    results = []
    for adapter in all_engines():
        print(f"Benchmarking {adapter.name}...")
        result = benchmark_engine(adapter, model=model, on_progress=lambda line: print(f"  {line}"))
        results.append(result)

    print("\nResults:")
    for r in results:
        if not r.installed:
            print(f"  {r.engine}: not installed, skipped")
            continue
        if r.avg_tokens_per_second is None:
            print(f"  {r.engine}: FAILED ({r.error or 'no successful runs'})")
            continue
        print(f"  {r.engine}: avg {r.avg_tokens_per_second} tok/s")

    best = recommend(results)
    if best:
        print(f"\nRecommendation: {best.engine} -- {best.reason}")
    else:
        print("\nNo engine produced a usable result -- nothing to recommend.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
