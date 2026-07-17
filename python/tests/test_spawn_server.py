from __future__ import annotations

import time

import pytest

from inferbench.errors import EngineStartTimeoutError
from inferbench.harness.spawn_server import spawn_server_and_wait_ready


def test_raises_start_timeout_quickly_when_nothing_answers_the_ready_check():
    start = time.monotonic()
    with pytest.raises(EngineStartTimeoutError):
        spawn_server_and_wait_ready(
            engine="test-engine",
            command="sleep",
            args=["30"],  # a harmless long-running process that never opens a port
            ready_check_url="http://127.0.0.1:1/never-listening",  # port 1 -- nothing listens here
            timeout_ms=300,
            poll_interval_ms=50,
        )
    elapsed = time.monotonic() - start
    # Should resolve close to the 300ms timeout, not hang for the real
    # 5-minute production default.
    assert elapsed < 2.0


def test_raises_immediately_if_the_process_exits_before_becoming_ready():
    with pytest.raises(RuntimeError, match="exited early"):
        spawn_server_and_wait_ready(
            engine="test-engine",
            command="false",  # exits immediately with a non-zero code
            args=[],
            ready_check_url="http://127.0.0.1:1/never-listening",
            timeout_ms=5000,
            poll_interval_ms=50,
        )
