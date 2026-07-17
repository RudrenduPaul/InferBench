from __future__ import annotations

from typing import Callable, List, Optional

import pytest

from inferbench.types import StartedServer


class FakeAdapter:
    """A minimal stand-in for LlamaCppAdapter/OmlxAdapter, mirroring the
    hand-rolled fake adapters the TypeScript suite builds in
    benchmark.test.ts (makeWorkingAdapter / makeUninstalledAdapter /
    makeFailingStartAdapter)."""

    def __init__(
        self,
        name: str,
        *,
        installed: bool = True,
        start_error: Optional[Exception] = None,
        stop: Optional[Callable[[], None]] = None,
    ) -> None:
        self.name = name
        self.binary = f"{name}-binary"
        self._installed = installed
        self._start_error = start_error
        self.stop_calls = 0
        self._stop = stop or (lambda: None)

    def is_installed(self) -> bool:
        return self._installed

    def start_server(self, *, model: str, port: int, timeout_ms: int, verbose: bool = False) -> StartedServer:
        if self._start_error is not None:
            raise self._start_error

        def stop() -> None:
            self.stop_calls += 1
            self._stop()

        return StartedServer(
            process=None,  # type: ignore[arg-type] -- fake adapter never spawns a real process
            base_url="http://fake",
            model_id="test-model",
            stop=stop,
        )


@pytest.fixture()
def fake_urlopen_sequence(monkeypatch):
    """Stubs urllib.request.urlopen to return a scripted sequence of fake
    HTTP responses, mirroring the vi.stubGlobal("fetch", ...) pattern used
    throughout the TypeScript harness/benchmark tests."""

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

    def _install(responses: List[bytes], statuses: Optional[List[int]] = None):
        calls = {"count": 0}

        def _fake_urlopen(*args, **kwargs):
            i = min(calls["count"], len(responses) - 1)
            calls["count"] += 1
            status = statuses[i] if statuses else 200
            return _FakeResponse(status, responses[i])

        import inferbench.harness.measure as measure_module

        monkeypatch.setattr(measure_module.urllib.request, "urlopen", _fake_urlopen)
        return calls

    return _install
