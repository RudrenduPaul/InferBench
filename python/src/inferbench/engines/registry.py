"""Ported from src/engines/registry.ts."""
from __future__ import annotations

from typing import Callable, Dict, List

from ..errors import UsageError
from ..types import EngineAdapter
from .llamacpp import LlamaCppAdapter
from .omlx import OmlxAdapter

_ADAPTERS: Dict[str, Callable[[], EngineAdapter]] = {
    "omlx": OmlxAdapter,
    "llama.cpp": LlamaCppAdapter,
}

SUPPORTED_ENGINES: List[str] = list(_ADAPTERS.keys())


def resolve_engines(names: List[str]) -> List[EngineAdapter]:
    """Dedupes and validates a user-supplied --engines list."""
    deduped = list(dict.fromkeys(names))
    unknown = [n for n in deduped if n not in _ADAPTERS]
    if unknown:
        raise UsageError(
            f"Unknown engine(s): {', '.join(unknown)}. Supported: {', '.join(SUPPORTED_ENGINES)}"
        )
    return [_ADAPTERS[n]() for n in deduped]


def all_engines() -> List[EngineAdapter]:
    return [_ADAPTERS[n]() for n in SUPPORTED_ENGINES]
