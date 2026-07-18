"""
Ported from src/engines/llamacpp.ts. `model` is treated as a Hugging Face
repo spec (e.g. "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M") -- llama.cpp's
own `-hf` flag downloads and caches it automatically, no manual step needed.
"""
from __future__ import annotations

import subprocess

from ..errors import EngineNotFoundError, UsageError
from ..harness.spawn_server import spawn_server_and_wait_ready
from ..types import StartedServer

_BINARY = "llama-server"


class LlamaCppAdapter:
    name = "llama.cpp"
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
        if model.startswith("-"):
            raise UsageError(
                f'Invalid --model value "{model}": cannot start with "-" '
                "(would be parsed as a flag by llama-server, not a model spec)"
            )
        spawned = spawn_server_and_wait_ready(
            engine=self.name,
            command=_BINARY,
            args=["-hf", model, "--port", str(port), "--host", "127.0.0.1"],
            ready_check_url=f"http://127.0.0.1:{port}/v1/models",
            timeout_ms=timeout_ms,
            verbose=verbose,
        )
        return StartedServer(
            process=spawned.process,
            base_url=f"http://127.0.0.1:{port}",
            model_id="default",
            stop=spawned.stop,
        )
