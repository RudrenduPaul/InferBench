"""
Ported from src/harness/measure.ts. Sends one timed chat-completion request
to an engine's OpenAI-compatible server and measures wall-clock time plus
reported token counts -- the ONE shared measurement code path for every
engine (the architecture decision that replaced per-engine benchmark-CLI
parsing; omlx has no CLI benchmark tool at all, verified against its real
README before the original tool's adapter code was written).

Elapsed time is measured across the FULL response body, not just the
headers: urlopen() returns once headers arrive, before the response body
(and therefore generation) has finished streaming. The original TypeScript
harness had a real bug here once -- measuring right after `await fetch(...)`
resolved, which produced a physically impossible 64,646 tok/s during a live
end-to-end run before it was caught and fixed. This port measures after
`response.read()` completes, deliberately not reintroducing that bug.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from ..errors import BenchmarkParseError, EngineRequestTimeoutError
from ..types import CompletionResult


@dataclass
class TimedCompletionOptions:
    engine: str
    base_url: str
    model_id: str
    prompt: str
    max_tokens: int
    timeout_ms: int


def timed_completion(opts: TimedCompletionOptions) -> CompletionResult:
    body = json.dumps(
        {
            "model": opts.model_id,
            "messages": [{"role": "user", "content": opts.prompt}],
            "max_tokens": opts.max_tokens,
            "stream": False,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{opts.base_url}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.perf_counter()
    try:
        response = urllib.request.urlopen(  # noqa: S310 -- fixed, internally-constructed URL only
            request, timeout=opts.timeout_ms / 1000
        )
        raw_bytes = response.read()
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8", errors="replace") if err.fp else ""
        raise BenchmarkParseError(opts.engine, f"HTTP {err.code}: {error_body}") from err
    except (socket.timeout, TimeoutError) as err:
        raise EngineRequestTimeoutError(opts.engine, opts.timeout_ms) from err
    except urllib.error.URLError as err:
        if isinstance(err.reason, (socket.timeout, TimeoutError)):
            raise EngineRequestTimeoutError(opts.engine, opts.timeout_ms) from err
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    raw_text = raw_bytes.decode("utf-8", errors="replace")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as err:
        raise BenchmarkParseError(opts.engine, raw_text) from err

    usage = payload.get("usage") if isinstance(payload, dict) else None
    completion_tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
    if not isinstance(completion_tokens, (int, float)) or isinstance(completion_tokens, bool):
        completion_tokens = None

    prompt_tokens_details = usage.get("prompt_tokens_details") if isinstance(usage, dict) else None
    cached_raw = (
        prompt_tokens_details.get("cached_tokens") if isinstance(prompt_tokens_details, dict) else None
    )
    cached_prompt_tokens = (
        int(cached_raw) if isinstance(cached_raw, (int, float)) and not isinstance(cached_raw, bool) else 0
    )

    tokens_per_second = (
        completion_tokens / (elapsed_ms / 1000) if completion_tokens and elapsed_ms > 0 else None
    )

    return CompletionResult(
        elapsed_ms=round(elapsed_ms),
        completion_tokens=int(completion_tokens) if completion_tokens is not None else None,
        cached_prompt_tokens=cached_prompt_tokens,
        tokens_per_second=round(tokens_per_second, 2) if tokens_per_second is not None else None,
    )
