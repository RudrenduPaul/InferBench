from __future__ import annotations

import pytest

from inferbench.engines.registry import SUPPORTED_ENGINES, all_engines, resolve_engines
from inferbench.errors import UsageError


def test_dedupes_repeated_engine_names():
    engines = resolve_engines(["omlx", "omlx", "llama.cpp"])
    assert len(engines) == 2
    assert sorted(e.name for e in engines) == ["llama.cpp", "omlx"]


def test_raises_usage_error_for_an_unknown_engine():
    with pytest.raises(UsageError):
        resolve_engines(["not-a-real-engine"])


def test_lists_the_unknown_engine_name_and_supported_engines_in_the_error():
    with pytest.raises(UsageError) as exc_info:
        resolve_engines(["bogus"])
    message = str(exc_info.value)
    assert "bogus" in message
    assert "omlx" in message
    assert "llama.cpp" in message


def test_all_engines_returns_one_adapter_per_supported_engine():
    assert len(all_engines()) == len(SUPPORTED_ENGINES)
