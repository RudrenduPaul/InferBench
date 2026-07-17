from __future__ import annotations

import subprocess

import pytest

from inferbench.engines.llamacpp import LlamaCppAdapter
from inferbench.errors import EngineNotFoundError


def test_is_installed_returns_true_when_the_binary_check_succeeds(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    adapter = LlamaCppAdapter()
    assert adapter.is_installed() is True


def test_is_installed_returns_false_when_the_binary_check_raises(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("command not found")

    monkeypatch.setattr(subprocess, "run", _raise)
    adapter = LlamaCppAdapter()
    assert adapter.is_installed() is False


def test_start_server_raises_engine_not_found_when_binary_missing(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("command not found")

    monkeypatch.setattr(subprocess, "run", _raise)
    adapter = LlamaCppAdapter()
    with pytest.raises(EngineNotFoundError):
        adapter.start_server(model="foo", port=9999, timeout_ms=100)
