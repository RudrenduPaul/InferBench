from __future__ import annotations

import json

import pytest

import inferbench.harness.measure as measure_module
from inferbench.benchmark import benchmark_engine
from tests.conftest import FakeAdapter


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


def _stub_urlopen_with_token_counts(monkeypatch, token_counts):
    calls = {"count": 0}

    def _fake_urlopen(*args, **kwargs):
        tokens = token_counts[min(calls["count"], len(token_counts) - 1)]
        calls["count"] += 1
        body = json.dumps(
            {"usage": {"completion_tokens": tokens, "prompt_tokens_details": {"cached_tokens": 0}}}
        ).encode("utf-8")
        return _FakeResponse(200, body)

    monkeypatch.setattr(measure_module.urllib.request, "urlopen", _fake_urlopen)
    return calls


def test_reports_installed_false_and_never_raises_when_the_binary_is_missing():
    adapter = FakeAdapter("phantom-engine", installed=False)
    result = benchmark_engine(adapter, model="any")
    assert result.installed is False
    assert result.avg_tokens_per_second is None
    assert result.runs == []


def test_reports_a_failure_result_instead_of_raising_when_the_server_fails_to_start():
    adapter = FakeAdapter("broken-engine", start_error=RuntimeError("could not bind port"))
    result = benchmark_engine(adapter, model="any")
    assert result.installed is True
    assert result.error is not None
    assert "could not bind port" in result.error
    assert result.avg_tokens_per_second is None


def test_calls_on_progress_with_per_engine_status_lines():
    adapter = FakeAdapter("progress-engine", installed=False)
    lines = []
    benchmark_engine(adapter, model="any", on_progress=lines.append)
    assert any("not installed" in line for line in lines)


def test_runs_the_warmup_call_plus_the_full_prompt_set_and_aggregates_real_tok_s(monkeypatch):
    # 8 prompt runs + 1 warm-up = 9 urlopen calls; token counts chosen so
    # avg/min/max are all distinct and easy to assert on.
    _stub_urlopen_with_token_counts(monkeypatch, [5, 10, 20, 30, 15, 25, 35, 5, 40])
    adapter = FakeAdapter("fake-engine")
    progress_lines = []

    result = benchmark_engine(
        adapter,
        model="test-model",
        prompts=["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"],
        on_progress=progress_lines.append,
    )

    assert result.installed is True
    assert len(result.runs) == 8
    assert all(r.ok for r in result.runs)
    assert result.avg_tokens_per_second > 0
    assert result.min_tokens_per_second <= result.max_tokens_per_second
    assert any("warming up" in line for line in progress_lines)
    assert any("[8/8]" in line for line in progress_lines)


def test_stops_the_server_even_if_a_prompt_run_fails_mid_sweep(monkeypatch):
    adapter = FakeAdapter("flaky-engine")
    calls = {"count": 0}

    def _fake_urlopen(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise ConnectionError("connection reset")
        body = json.dumps({"usage": {"completion_tokens": 10}}).encode("utf-8")
        return _FakeResponse(200, body)

    monkeypatch.setattr(measure_module.urllib.request, "urlopen", _fake_urlopen)

    result = benchmark_engine(adapter, model="test-model", prompts=["p1"])

    assert result.runs[0].ok is False
    assert result.runs[0].error is not None
    assert "connection reset" in result.runs[0].error
    assert adapter.stop_calls == 1


def test_reports_a_failure_result_when_the_warmup_call_itself_fails(monkeypatch):
    def _raise(*args, **kwargs):
        raise ConnectionError("warm-up connection refused")

    monkeypatch.setattr(measure_module.urllib.request, "urlopen", _raise)
    adapter = FakeAdapter("cold-engine")
    result = benchmark_engine(adapter, model="test-model")
    assert result.error is not None
    assert "warm-up failed" in result.error
    assert result.avg_tokens_per_second is None


def test_never_lets_one_adapters_failure_affect_a_second_adapters_own_result():
    broken = FakeAdapter("broken", start_error=RuntimeError("boom"))
    missing = FakeAdapter("missing", installed=False)

    result_broken = benchmark_engine(broken, model="any")
    result_missing = benchmark_engine(missing, model="any")

    assert result_broken.error is not None
    assert "boom" in result_broken.error
    assert result_missing.installed is False
