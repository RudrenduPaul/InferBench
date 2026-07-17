"""
Ported from src/report/json.ts, extended with a snake_case -> camelCase
key conversion so a report written by this CLI's --out is field-for-field
compatible with the npm CLI's own JSON report (both usable by the same
downstream tooling) -- see docs/concepts.md.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from ..types import BenchmarkReport


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


def write_json_report(report: BenchmarkReport, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(report_to_dict(report), handle, indent=2)
