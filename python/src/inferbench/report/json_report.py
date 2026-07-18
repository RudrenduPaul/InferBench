"""
Ported from src/report/json.ts, extended with a snake_case -> camelCase
key conversion so a report written by this CLI's --out is field-for-field
compatible with the npm CLI's own JSON report (both usable by the same
downstream tooling) -- see docs/concepts.md.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any, Dict

from ..types import BenchmarkReport


class UnsafeOutputPathError(ValueError):
    pass


def _to_camel_case(key: str) -> str:
    head, *tail = key.split("_")
    return head + "".join(part.title() for part in tail)


def _camelize(value: Any) -> Any:
    if isinstance(value, dict):
        return {_to_camel_case(k): _camelize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_camelize(v) for v in value]
    return value


def report_to_dict(report: BenchmarkReport) -> Dict[str, Any]:
    """BenchmarkReport never holds a StartedServer (that only lives on the
    adapter's return value during a run, not in the final report), so a
    plain dataclasses.asdict() is safe here -- nothing unconvertible in the
    tree."""
    return _camelize(asdict(report))


# --out is a plain CLI flag today, but this CLI is also meant to be invoked
# programmatically by agents that may derive the value from less-trusted
# input (a fetched benchmark config, an LLM-generated argument list, etc).
# A relative path containing ".." segments can escape the intended output
# location entirely (--out ../../../etc/cron.d/x) -- reject any --out value
# that resolves outside the current working directory. An explicit absolute
# path is still allowed: that's a value the caller typed/passed directly,
# not one that silently escaped via traversal.
def _assert_safe_output_path(file_path: str) -> None:
    if os.path.isabs(file_path):
        return
    cwd = os.path.realpath(os.getcwd())
    resolved = os.path.realpath(os.path.join(cwd, file_path))
    if resolved != cwd and not resolved.startswith(cwd + os.sep):
        raise UnsafeOutputPathError(
            f'--out "{file_path}" resolves outside the current working directory '
            f"({resolved}). Pass an absolute path if you intend to write outside "
            "the working directory."
        )


def write_json_report(report: BenchmarkReport, file_path: str) -> None:
    _assert_safe_output_path(file_path)
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(report_to_dict(report), handle, indent=2)
