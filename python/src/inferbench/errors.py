"""
Exception hierarchy, ported 1:1 from src/errors.ts. Every error message is
kept identical in wording to the TypeScript original so the two CLIs report
the same failure text for the same underlying condition.
"""
from __future__ import annotations


class EngineNotFoundError(Exception):
    def __init__(self, engine: str, binary: str) -> None:
        self.engine = engine
        self.binary = binary
        super().__init__(f'{engine}: binary "{binary}" not found on PATH -- skipped')


class EngineStartTimeoutError(Exception):
    def __init__(self, engine: str, timeout_ms: int) -> None:
        self.engine = engine
        self.timeout_ms = timeout_ms
        super().__init__(f"{engine}: server did not become ready within {timeout_ms}ms")


class EngineRequestTimeoutError(Exception):
    def __init__(self, engine: str, timeout_ms: int) -> None:
        self.engine = engine
        self.timeout_ms = timeout_ms
        super().__init__(f"{engine}: request timed out after {timeout_ms}ms")


class BenchmarkParseError(Exception):
    def __init__(self, engine: str, raw_output: str) -> None:
        self.engine = engine
        self.raw_output = raw_output
        super().__init__(f"{engine}: could not parse benchmark response")


class NoEnginesFoundError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "No supported engines found on this machine. Install omlx (brew install omlx) "
            "or llama.cpp (brew install llama.cpp) and try again."
        )


class UsageError(Exception):
    """Raised for invalid CLI input recognized at the library layer (e.g. an
    unknown --engines name). Distinct from argparse's own parse errors,
    which exit 2 directly -- see cli.py."""
