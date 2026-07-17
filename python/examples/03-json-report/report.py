#!/usr/bin/env python3
"""
The agent-native path: build a full BenchmarkReport in-process (no CLI
subprocess) and serialize it to JSON with the same camelCase field names
the npm CLI's own --json output uses -- see docs/concepts.md for why the
JSON shape is kept cross-language-compatible even though the native Python
API is snake_case.

Usage:
    python3 report.py <model-spec> [output-file]

Example:
    python3 report.py qwen2.5-1.5b-instruct-4bit report.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from inferbench import all_engines, benchmark_engine, detect_hardware, recommend
from inferbench.report.json_report import report_to_dict
from inferbench.types import BenchmarkReport


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <model-spec> [output-file]", file=sys.stderr)
        return 2

    model = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    hardware = detect_hardware()
    results = [benchmark_engine(adapter, model=model) for adapter in all_engines()]

    report = BenchmarkReport(
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        hardware=hardware,
        model=model,
        engines=results,
        recommendation=recommend(results),
    )

    payload = report_to_dict(report)
    text = json.dumps(payload, indent=2)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"Wrote report to {out_path}")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
