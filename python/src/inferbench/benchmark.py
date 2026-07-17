"""
Ported from src/benchmark.ts. Benchmarks a single engine. Never raises for
an engine-level failure (not installed, server start timeout, request
failure) -- engines are isolated from each other by design, so one bad
engine never blocks results from the others. Callers get a result object
with installed=False or per-run errors instead.
"""
from __future__ import annotations

from typing import Callable, List, Optional

from .harness.measure import TimedCompletionOptions, timed_completion
from .prompts import DEFAULT_PROMPTS, WARMUP_PROMPT
from .types import EngineAdapter, EngineBenchmarkResult, PromptRunResult

DEFAULT_MAX_TOKENS = 200
DEFAULT_SERVER_START_TIMEOUT_MS = 5 * 60 * 1000
DEFAULT_REQUEST_TIMEOUT_MS = 2 * 60 * 1000

_next_port = 41000


def _claim_port() -> int:
    global _next_port
    port = _next_port
    _next_port += 1
    return port


def benchmark_engine(
    adapter: EngineAdapter,
    *,
    model: str,
    max_tokens: Optional[int] = None,
    server_start_timeout_ms: Optional[int] = None,
    request_timeout_ms: Optional[int] = None,
    prompts: Optional[List[str]] = None,
    verbose: bool = False,
    on_progress: Optional[Callable[[str], None]] = None,
) -> EngineBenchmarkResult:
    progress = on_progress or (lambda _line: None)
    prompt_list = prompts if prompts is not None else DEFAULT_PROMPTS
    tokens_cap = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS

    if not adapter.is_installed():
        progress(f"{adapter.name}: not installed, skipped")
        return EngineBenchmarkResult(
            engine=adapter.name,
            installed=False,
            error=f'binary "{adapter.binary}" not found',
        )

    progress(f"{adapter.name}: starting server...")
    try:
        server = adapter.start_server(
            model=model,
            port=_claim_port(),
            timeout_ms=server_start_timeout_ms or DEFAULT_SERVER_START_TIMEOUT_MS,
            verbose=verbose,
        )
    except Exception as err:  # noqa: BLE001 -- any start-up failure reports as a failed result, never raises
        message = str(err)
        progress(f"{adapter.name}: failed to start ({message})")
        return EngineBenchmarkResult(engine=adapter.name, installed=True, error=message)

    try:
        progress(f"{adapter.name}: warming up...")
        try:
            timed_completion(
                TimedCompletionOptions(
                    engine=adapter.name,
                    base_url=server.base_url,
                    model_id=server.model_id,
                    prompt=WARMUP_PROMPT,
                    max_tokens=16,
                    timeout_ms=request_timeout_ms or DEFAULT_REQUEST_TIMEOUT_MS,
                )
            )
        except Exception as err:  # noqa: BLE001 -- any warm-up failure reports as a failed result
            message = str(err)
            progress(f"{adapter.name}: warm-up failed ({message})")
            return EngineBenchmarkResult(
                engine=adapter.name,
                installed=True,
                error=f"warm-up failed: {message}",
            )

        runs: List[PromptRunResult] = []
        for i, prompt in enumerate(prompt_list):
            progress(f"{adapter.name}: [{i + 1}/{len(prompt_list)}] benchmarking...")
            try:
                result = timed_completion(
                    TimedCompletionOptions(
                        engine=adapter.name,
                        base_url=server.base_url,
                        model_id=server.model_id,
                        prompt=prompt,
                        max_tokens=tokens_cap,
                        timeout_ms=request_timeout_ms or DEFAULT_REQUEST_TIMEOUT_MS,
                    )
                )
                runs.append(PromptRunResult(prompt=prompt, ok=True, result=result))
            except Exception as err:  # noqa: BLE001 -- one failed prompt must not abort the sweep
                runs.append(PromptRunResult(prompt=prompt, ok=False, error=str(err)))

        valid = [
            r.result.tokens_per_second
            for r in runs
            if r.ok and r.result is not None and r.result.tokens_per_second
        ]

        return EngineBenchmarkResult(
            engine=adapter.name,
            installed=True,
            runs=runs,
            avg_tokens_per_second=round(sum(valid) / len(valid), 2) if valid else None,
            min_tokens_per_second=min(valid) if valid else None,
            max_tokens_per_second=max(valid) if valid else None,
        )
    finally:
        server.stop()
