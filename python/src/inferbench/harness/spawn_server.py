"""
Ported from src/harness/spawn-server.ts. Spawns a long-running engine
server process and polls a URL until it responds, so callers get a server
that is actually ready rather than racing against startup.

Security note: `command` and `args` are always a fixed argv list passed to
subprocess.Popen with no shell involved (no shell=True anywhere in this
module or its callers) -- the model spec a user passes on --model becomes
a single argv element, never string-concatenated into a shell command, so
there is no command-injection path through it. This mirrors the same
argv-array discipline the original TypeScript harness documents in its own
comments.
"""
from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, List, Optional

from ..errors import EngineStartTimeoutError


@dataclass
class SpawnedServer:
    process: subprocess.Popen
    stop: Callable[[], None]


def spawn_server_and_wait_ready(
    *,
    engine: str,
    command: str,
    args: List[str],
    ready_check_url: str,
    timeout_ms: int,
    poll_interval_ms: int = 500,
    verbose: bool = False,
) -> SpawnedServer:
    stdio = None if verbose else subprocess.DEVNULL
    process = subprocess.Popen([command, *args], stdout=stdio, stderr=stdio)  # noqa: S603 -- fixed argv, no shell

    def stop() -> None:
        if process.poll() is None:
            process.kill()

    deadline = time.monotonic() + timeout_ms / 1000
    last_error: Optional[BaseException] = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"{engine}: process exited early (code {process.returncode}) before becoming ready"
            )
        try:
            with urllib.request.urlopen(ready_check_url, timeout=2) as response:  # noqa: S310
                if 200 <= response.status < 300:
                    return SpawnedServer(process=process, stop=stop)
        except Exception as err:  # noqa: BLE001 -- polling loop; any failure just means "not ready yet"
            last_error = err
        time.sleep(poll_interval_ms / 1000)

    stop()
    timeout_err = EngineStartTimeoutError(engine, timeout_ms)
    if last_error is not None:
        timeout_err.__cause__ = last_error
    raise timeout_err
