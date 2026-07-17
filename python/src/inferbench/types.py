"""
Shared data types, ported from src/types.ts. Field names follow Python
convention (snake_case) rather than the TypeScript originals' camelCase --
the JSON report writer (report/json_report.py) converts back to camelCase
so a --json/--out report is field-for-field compatible with the npm CLI's
own JSON output, even though the two libraries' native call shapes differ.
See docs/concepts.md for the full data model and the snake_case/camelCase
note.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class HardwareProfile:
    platform: str
    arch: str
    total_memory_gb: float
    cpu_model: str
    is_apple_silicon: bool


@dataclass
class StartedServer:
    process: subprocess.Popen
    base_url: str
    model_id: str
    stop: Callable[[], None]


@dataclass
class CompletionResult:
    elapsed_ms: float
    completion_tokens: Optional[int]
    cached_prompt_tokens: int
    tokens_per_second: Optional[float]


@dataclass
class PromptRunResult:
    prompt: str
    ok: bool
    error: Optional[str] = None
    result: Optional[CompletionResult] = None


@dataclass
class EngineBenchmarkResult:
    engine: str
    installed: bool
    error: Optional[str] = None
    runs: List[PromptRunResult] = field(default_factory=list)
    avg_tokens_per_second: Optional[float] = None
    min_tokens_per_second: Optional[float] = None
    max_tokens_per_second: Optional[float] = None


@dataclass
class Recommendation:
    engine: str
    reason: str


@dataclass
class BenchmarkReport:
    timestamp: str
    hardware: HardwareProfile
    model: str
    engines: List[EngineBenchmarkResult]
    recommendation: Optional[Recommendation]


@runtime_checkable
class EngineAdapter(Protocol):
    """Structural type -- any object with this shape (name, binary,
    is_installed(), start_server(...)) works as an adapter, mirroring the
    TS interface's duck-typed usage. LlamaCppAdapter and OmlxAdapter both
    satisfy this without inheriting from it explicitly."""

    name: str
    binary: str

    def is_installed(self) -> bool: ...

    def start_server(
        self,
        *,
        model: str,
        port: int,
        timeout_ms: int,
        verbose: bool = False,
    ) -> StartedServer: ...
