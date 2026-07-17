"""
Ported from src/engines/omlx.ts.

omlx has no CLI benchmark tool of its own (verified against its real
README -- its "Performance Benchmark" feature is a GUI-only, one-click
action in its admin dashboard). This adapter only starts the server; all
measurement goes through the shared HTTP harness in harness/measure.py,
same as every other engine.

`model` is treated as a model-directory subdirectory name under
~/.omlx/models/<model> -- omlx's `serve` command has no positional model
argument and discovers models from --model-dir subdirectories. Unlike
llama.cpp, omlx does not auto-download an arbitrary Hugging Face repo from
a CLI flag, so the model must already be present locally -- an honest v0.1
limitation, not hidden from the user.
"""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

from ..errors import EngineNotFoundError, EngineStartTimeoutError
from ..harness.spawn_server import spawn_server_and_wait_ready
from ..types import StartedServer

_BINARY = "omlx"


class OmlxAdapter:
    name = "omlx"
    binary = _BINARY

    def is_installed(self) -> bool:
        try:
            subprocess.run(  # noqa: S603, S607 -- fixed argv, binary name only, no shell
                [_BINARY, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except (OSError, subprocess.CalledProcessError):
            return False

    def start_server(
        self,
        *,
        model: str,
        port: int,
        timeout_ms: int,
        verbose: bool = False,
    ) -> StartedServer:
        if not self.is_installed():
            raise EngineNotFoundError(self.name, _BINARY)

        model_dir = str(Path.home() / ".omlx" / "models")
        spawned = spawn_server_and_wait_ready(
            engine=self.name,
            command=_BINARY,
            args=["serve", "--model-dir", model_dir, "--port", str(port)],
            ready_check_url=f"http://127.0.0.1:{port}/v1/models",
            timeout_ms=timeout_ms,
            verbose=verbose,
        )

        model_id = self._resolve_model_id(port, model)
        if not model_id:
            spawned.stop()
            raise EngineStartTimeoutError(self.name, timeout_ms)

        return StartedServer(
            process=spawned.process,
            base_url=f"http://127.0.0.1:{port}",
            model_id=model_id,
            stop=spawned.stop,
        )

    def _resolve_model_id(self, port: int, requested_model: str) -> Optional[str]:
        try:
            with urllib.request.urlopen(  # noqa: S310 -- fixed, internally-constructed loopback URL
                f"http://127.0.0.1:{port}/v1/models", timeout=5
            ) as response:
                if response.status != 200:
                    return None
                payload: Any = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError):
            return None

        models = payload.get("data") if isinstance(payload, dict) else None
        if not models:
            return None
        exact = next((m for m in models if m.get("id") == requested_model), None)
        return exact["id"] if exact else models[0].get("id")
