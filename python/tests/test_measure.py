from __future__ import annotations

import json
import socket
import time
import urllib.error

import pytest

import inferbench.harness.measure as measure_module
from inferbench.errors import BenchmarkParseError, EngineRequestTimeoutError
from inferbench.harness.measure import TimedCompletionOptions, timed_completion


def _opts(**overrides):
    base = dict(
        engine="test-engine",
        base_url="http://fake",
        model_id="test-model",
        prompt="hi",
        max_tokens=16,
        timeout_ms=5000,
    )
    base.update(overrides)
    return TimedCompletionOptions(**base)


class _SlowBodyResponse:
    """Simulates a server whose headers arrive instantly but whose body
    (i.e. generation) takes 100ms to finish -- the same shape of gap that
    caused a real bug in the original TypeScript harness (measuring right
    after fetch() resolved, which only captures header arrival, produced a
    physically impossible 64,646 tok/s during a live end-to-end run)."""

    status = 200

    def read(self) -> bytes:
        time.sleep(0.1)
        return json.dumps(
            {"usage": {"completion_tokens": 10, "prompt_tokens_details": {"cached_tokens": 0}}}
        ).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_measures_elapsed_time_across_the_full_response_body_not_just_headers(monkeypatch):
    monkeypatch.setattr(measure_module.urllib.request, "urlopen", lambda *a, **k: _SlowBodyResponse())

    result = timed_completion(_opts())

    # If this ever regresses to measuring only the time up to when headers
    # arrive, elapsed_ms would be ~0-5ms and tokens_per_second would blow up
    # into the thousands, exactly like the real bug this guards against.
    assert result.elapsed_ms >= 90
    assert result.completion_tokens == 10
    assert result.tokens_per_second is not None
    assert result.tokens_per_second < 200


class _FakeResponse:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_parses_cached_prompt_tokens_when_present(monkeypatch):
    body = json.dumps(
        {"usage": {"completion_tokens": 5, "prompt_tokens_details": {"cached_tokens": 39}}}
    ).encode("utf-8")
    monkeypatch.setattr(measure_module.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(200, body))
    result = timed_completion(_opts())
    assert result.cached_prompt_tokens == 39


def test_defaults_cached_prompt_tokens_to_zero_when_absent(monkeypatch):
    body = json.dumps({"usage": {"completion_tokens": 5}}).encode("utf-8")
    monkeypatch.setattr(measure_module.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(200, body))
    result = timed_completion(_opts())
    assert result.cached_prompt_tokens == 0


def test_raises_benchmark_parse_error_on_malformed_json(monkeypatch):
    monkeypatch.setattr(
        measure_module.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(200, b"not json")
    )
    with pytest.raises(BenchmarkParseError):
        timed_completion(_opts())


def test_raises_benchmark_parse_error_on_a_non_ok_http_response(monkeypatch):
    def _raise(*args, **kwargs):
        err = urllib.error.HTTPError("http://fake", 500, "internal error", {}, None)
        raise err

    monkeypatch.setattr(measure_module.urllib.request, "urlopen", _raise)
    with pytest.raises(BenchmarkParseError):
        timed_completion(_opts())


def test_raises_engine_request_timeout_error_on_socket_timeout(monkeypatch):
    def _raise(*args, **kwargs):
        raise socket.timeout("timed out")

    monkeypatch.setattr(measure_module.urllib.request, "urlopen", _raise)
    with pytest.raises(EngineRequestTimeoutError):
        timed_completion(_opts(timeout_ms=50))


def test_returns_none_tokens_per_second_when_completion_tokens_is_missing(monkeypatch):
    body = json.dumps({"usage": {}}).encode("utf-8")
    monkeypatch.setattr(measure_module.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(200, body))
    result = timed_completion(_opts())
    assert result.completion_tokens is None
    assert result.tokens_per_second is None
