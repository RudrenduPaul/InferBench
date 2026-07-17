# Concepts

## The measurement pipeline

Both the npm and PyPI packages run the same pipeline (TypeScript:
`src/benchmark.ts` + `src/harness/`; Python: `inferbench/benchmark.py` +
`inferbench/harness/`):

```
adapter.is_installed()  -> False: return {installed: false}, never raises
     |
     v
adapter.start_server()   -> spawns the engine's own OpenAI-compatible HTTP
     |                       server as a real subprocess (argv list, never
     |                       a shell string), polls a readiness URL until
     |                       it responds
     v
warm-up request           -> one throwaway completion, to absorb any
     |                        first-request-is-slow cost before real
     |                        measurement starts
     v
8 varied prompts, timed    -> each one a real HTTP POST to
individually                  /v1/chat/completions, timed across the FULL
     |                        response body (not just headers -- see below)
     v
avg / min / max tok/s       -> computed only from runs that both succeeded
                                and reported a non-zero completion-token
                                count
```

A benchmark result is always a structured value, never a thrown exception
-- one engine's failure (not installed, server timeout, a single failed
prompt mid-sweep) never blocks or corrupts another engine's result, and the
server is always stopped in a `finally`/`finally` block even if a prompt
run raises.

## Why elapsed time is measured across the full response body

Both engines' servers are started with `stream: false`, so each completion
comes back as a single HTTP response. The obvious-looking approach --
timing from just after the request is sent to just after the response
object resolves (`fetch()` in TypeScript, `urlopen()` in Python) -- is
wrong, because both of those calls return once the *headers* arrive, before
the response *body* (and therefore generation) is actually finished being
streamed back over the wire. The original TypeScript harness had this
exact bug once: it measured elapsed time right after `await fetch(...)`
resolved, which produced a physically impossible 64,646 tok/s during a real
end-to-end run before the bug was caught and fixed. Both distributions now
measure elapsed time after the response body has been fully read, and both
test suites carry a regression test for this specific gap
(`src/harness/measure.test.ts` / `python/tests/test_measure.py`).

## Why omlx and llama.cpp need different adapters

- **`llama.cpp`** exposes a `-hf <repo>:<quant>` flag on `llama-server`
  that downloads and caches an arbitrary Hugging Face repo automatically.
  `--model` for this engine is that Hugging Face repo spec.
- **`omlx`** has no equivalent flag. Its `serve` command only discovers
  models already present as subdirectories under `--model-dir` (this tool
  points that at `~/.omlx/models/`). `--model` for this engine is the
  subdirectory name of a model you have already downloaded there (via
  omlx's own admin dashboard, or `huggingface_hub`'s `snapshot_download`).

This is a genuine capability difference between the two engines, not an
inconsistency in this tool -- stated plainly rather than hidden behind a
single unified `--model` semantic that would only work for one of the two
engines.

## The hardware detector

`detect_hardware()` / `detectHardware()` reports platform, CPU architecture,
total system memory, the CPU model string, and whether the machine is
Apple Silicon (`darwin` + `arm64`). Node's `os` module provides all of this
directly; Python's standard library does not have one equivalent call, so
the Python port composes `sys.platform`, `platform.machine()`, POSIX
`os.sysconf()` for total memory, and two small, fixed-argv subprocess calls
(`sysctl -n machdep.cpu.brand_string` on macOS, `/proc/cpuinfo` parsing on
Linux) for the CPU model string -- see
`python/src/inferbench/hardware/detect.py` for the exact fallback chain.
Both implementations degrade to a safe default (`"unknown"` / `0.0`) rather
than raising if a given platform doesn't support a particular lookup.

## The recommendation rule

v0.1's rule is deliberately simple: the engine with the highest measured
average tokens/second among engines that were both installed and produced
at least one successful run. No memory-usage or cost weighting is applied
yet -- richer multi-factor scoring is intentionally deferred until real
usage shows this simple rule picks wrong recommendations. The
recommendation text always states explicitly that the result is
run-specific, not a universal ranking, because different models, different
hardware, or even different thermal conditions on the same machine can
change which engine wins.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | At least one engine was tested successfully (some engines may still individually show `not installed` or `FAILED` in the results). |
| `1` | A resolvable usage error (an unknown `--engines` name) or no supported engine was found installed at all (`NoEnginesFoundError`). |
| `2` (Python CLI only) | Invalid CLI input caught by `argparse` itself -- e.g. a missing required `--model` flag, or an unrecognized flag. The npm CLI's `commander`-based parser exits `1` for the same class of error; this is a documented, intentional divergence rather than a parity bug -- exit code `2` for a parse-time error is the standard Unix/argparse convention. |

## JSON report shape

`--json` / `--out <file>` serialize a `BenchmarkReport`. The Python CLI's
JSON output uses the same camelCase field names as the npm CLI's own
(`avgTokensPerSecond`, `cpuModel`, `isAppleSilicon`, ...) even though the
Python library's native Python API is snake_case (`avg_tokens_per_second`,
`cpu_model`, `is_apple_silicon`, ...) -- the JSON serializer in
`python/src/inferbench/report/json_report.py` converts one to the other, so
a report file produced by either CLI is field-for-field interchangeable
with downstream tooling that only reads the JSON, while each language's
native library API still follows that language's own naming convention.
