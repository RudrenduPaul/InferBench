#!/usr/bin/env python3
"""
Ported from src/cli.ts (which uses `commander`); this port uses the stdlib
`argparse` to avoid a CLI-framework dependency. Flags and defaults are kept
identical in name and meaning to the npm CLI. Console entry point:
`inferbench run [options]`, installed via the `inferbench` console-script
defined in python/pyproject.toml.

One deliberate, documented divergence from the TypeScript CLI: argparse's
own parse errors (a missing required --model, an unrecognized flag) exit
with code 2, the standard argparse/Unix convention, rather than commander's
exit code 1 for the same case. The "ran, but no supported engine was
installed" case still exits 1 on both CLIs, matching NoEnginesFoundError's
documented contract. See docs/concepts.md for the full exit-code table.
"""
from __future__ import annotations

import argparse
import json as json_module
import sys
from datetime import datetime, timezone
from typing import List

from .benchmark import benchmark_engine
from .engines.registry import SUPPORTED_ENGINES, all_engines, resolve_engines
from .errors import NoEnginesFoundError, UsageError
from .hardware.detect import detect_hardware
from .recommend.config import recommend
from .report.json_report import report_to_dict, write_json_report
from .types import BenchmarkReport

_VERSION = "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inferbench",
        description=(
            "Benchmarks local-LLM-inference engines (omlx, llama.cpp) on your own "
            "hardware, live."
        ),
    )
    parser.add_argument("--version", action="version", version=f"inferbench {_VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Benchmark installed engines against a model")
    run_parser.add_argument(
        "--model", required=True, help="Model spec (engine-specific, see README)"
    )
    run_parser.add_argument(
        "--engines",
        default=None,
        help=(
            "Comma-separated engines to test (default: all supported -- "
            f"{', '.join(SUPPORTED_ENGINES)})"
        ),
    )
    run_parser.add_argument(
        "--max-tokens", default="200", help="Max completion tokens per prompt"
    )
    run_parser.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON instead of a human table"
    )
    run_parser.add_argument("--out", default=None, help="Also write the full JSON report to this file")
    run_parser.add_argument(
        "--verbose", action="store_true", help="Show raw engine server stdout/stderr"
    )

    return parser


def _parse_max_tokens(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise UsageError(
            f'Invalid --max-tokens value "{value}": must be a whole number, e.g. --max-tokens 200'
        ) from None
    if parsed <= 0:
        raise UsageError(f'Invalid --max-tokens value "{value}": must be a positive number')
    return parsed


def _run_command(args: argparse.Namespace) -> None:
    adapters = resolve_engines(args.engines.split(",")) if args.engines else all_engines()
    max_tokens = _parse_max_tokens(args.max_tokens)

    hardware = detect_hardware()
    if not args.json:
        print(
            f"Hardware: {hardware.cpu_model} ({hardware.platform}/{hardware.arch}), "
            f"{hardware.total_memory_gb}GB\n"
        )

    results = []
    for adapter in adapters:
        result = benchmark_engine(
            adapter,
            model=args.model,
            max_tokens=max_tokens,
            verbose=args.verbose,
            on_progress=None if args.json else print,
        )
        results.append(result)

    if not any(r.installed for r in results):
        raise NoEnginesFoundError()

    report = BenchmarkReport(
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        hardware=hardware,
        model=args.model,
        engines=results,
        recommendation=recommend(results),
    )

    if args.out:
        write_json_report(report, args.out)

    if args.json:
        print(json_module.dumps(report_to_dict(report), indent=2))
        return

    print("\nResults:")
    for r in results:
        if not r.installed:
            print(f"  {r.engine}: not installed, skipped")
            continue
        if r.avg_tokens_per_second is None:
            print(f"  {r.engine}: FAILED ({r.error or 'no successful runs'})")
            continue
        n = sum(1 for run in r.runs if run.ok)
        print(
            f"  {r.engine}: avg {r.avg_tokens_per_second} tok/s "
            f"(range {r.min_tokens_per_second}-{r.max_tokens_per_second}, n={n})"
        )

    if report.recommendation:
        print(f"\nRecommendation: {report.recommendation.engine} -- {report.recommendation.reason}")

    if args.out:
        print(f"\nFull report: {args.out}")


def run_cli(argv: List[str]) -> int:
    """`argv` follows the sys.argv convention: argv[0] is the program name,
    the real arguments start at argv[1]. Returns the process exit code (0
    on a successful run with at least one engine tested; 1 on a usage error
    or when no supported engine is installed). Invalid CLI input calls
    sys.exit(2) directly via argparse, same as build_parser()'s own error
    handling."""
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.command != "run":
        parser.print_help()
        return 0

    try:
        _run_command(args)
        return 0
    except (UsageError, NoEnginesFoundError) as err:
        print(str(err), file=sys.stderr)
        return 1


def main() -> None:
    sys.exit(run_cli(sys.argv))


if __name__ == "__main__":
    main()
