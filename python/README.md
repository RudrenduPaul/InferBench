# inferbench-cli (Python)

Vendor-neutral benchmark for local-LLM-inference engines -- measures real
tokens/second for `omlx` and `llama.cpp` on your own hardware, live, and
recommends the faster engine for your exact machine and model. This
package is the Python distribution -- a genuine, independent port of the
npm package's TypeScript source, not a wrapper around the Node binary.

[![PyPI version](https://img.shields.io/pypi/v/inferbench-cli.svg)](https://pypi.org/project/inferbench-cli/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/RudrenduPaul/InferBench/blob/main/LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/inferbench-cli.svg)](https://pypi.org/project/inferbench-cli/)
[![CI](https://github.com/RudrenduPaul/InferBench/actions/workflows/ci.yml/badge.svg)](https://github.com/RudrenduPaul/InferBench/actions/workflows/ci.yml)

## Why this exists

Every local-inference engine publishes its own benchmark numbers, on its
own hardware, in its own README. None of them tell you which engine is
actually fastest on the machine sitting in front of you. InferBench starts
each engine's own OpenAI-compatible HTTP server on `127.0.0.1`, runs a
fixed, varied 8-prompt set through the exact same measurement code against
every engine, and reports the real, measured tokens/second -- not a number
copied from a blog post.

**Supported engines today: `omlx` and `llama.cpp`.** That is the complete
list this v0.1 release supports -- see [docs/concepts.md](https://github.com/RudrenduPaul/InferBench/blob/main/docs/concepts.md)
for why each engine needed its own adapter and what each one's real
constraints are.

## Install

```bash
pip install inferbench-cli
```

or with [uv](https://docs.astral.sh/uv/):

```bash
uv add inferbench-cli
```

**Publish status, stated plainly**: this package is built, tested, and
verified end to end (see "Verified" in
[CHANGELOG.md](https://github.com/RudrenduPaul/InferBench/blob/main/CHANGELOG.md)),
and is published to PyPI today. `pip install inferbench-cli` works -- see
[pypi.org/project/inferbench-cli](https://pypi.org/project/inferbench-cli/).

Zero third-party dependencies -- the CLI, the HTTP harness, and the
hardware detector are all built on the Python standard library
(`argparse`, `urllib.request`, `subprocess`, `os`). The complementary
JS/TS distribution installs the same way on the npm side:
`npm install -g inferbench-cli` (or `npx inferbench-cli run ...` to run it
once without installing) -- see the
[project README](https://github.com/RudrenduPaul/InferBench#readme) for
that package. Both are published and maintained together as first-class
packages.

Either package still requires at least one supported engine already
installed on your machine -- neither package installs an inference engine
for you:

- **llama.cpp**: `brew install llama.cpp` (macOS) or build from
  [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)
- **omlx**: `brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx`
  (Apple Silicon only)

## Quickstart

```bash
# llama.cpp -- pass a Hugging Face repo spec; llama.cpp downloads and
# caches it automatically, no manual step required
inferbench run --engines llama.cpp --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"

# omlx -- pass the model-directory subdirectory name under ~/.omlx/models/;
# omlx has no CLI download flow, so the model must already be present there
inferbench run --engines omlx --model "qwen2.5-1.5b-instruct-4bit"

# Both installed engines, machine-readable output, saved to a file
inferbench run --model "<spec>" --json --out report.json
```

**Known v0.1 limitation, carried over from the npm package and equally
true here:** `--model` means something different per engine (a
downloadable Hugging Face spec for llama.cpp, a pre-downloaded local
directory name for omlx), because the two engines have genuinely different
model-acquisition capabilities.

Or call the library directly (the agent-native path):

```python
from inferbench import benchmark_engine, detect_hardware, all_engines, recommend

hardware = detect_hardware()
results = [
    benchmark_engine(adapter, model="qwen2.5-1.5b-instruct-4bit")
    for adapter in all_engines()
]
best = recommend(results)
if best:
    print(f"{best.engine}: {best.reason}")
```

## CLI command reference

```
inferbench run [options]

Options:
  --model <spec>    Model spec (engine-specific, see Quickstart above)   [required]
  --engines <list>  Comma-separated engines to test (default: all installed --
                     omlx, llama.cpp)
  --max-tokens <n>  Max completion tokens per prompt (default: 200)
  --json            Output machine-readable JSON instead of a human table
  --out <file>      Also write the full JSON report to this file
  --verbose         Show raw engine server stdout/stderr
```

Exit code `0` on a successful run with at least one engine tested; `1` on
a resolvable usage error (e.g. an unknown `--engines` name) or when no
supported engine is installed. **One documented divergence from the npm
CLI**: a missing required flag (e.g. no `--model` at all) exits `2` here,
the standard `argparse`/Unix convention for a parse-time error, rather than
the npm CLI's `1` for the same case -- see
[docs/concepts.md](https://github.com/RudrenduPaul/InferBench/blob/main/docs/concepts.md)
for the full exit-code table.

## How the measurement works

Same architecture as the npm package, ported faithfully: InferBench does
not shell out to each engine's own benchmark tool and parse its output --
`omlx` has no CLI benchmark command at all (verified against its real
README; its "Performance Benchmark" feature is a GUI-only, one-click
action in its admin dashboard). Instead, this package starts each engine's
own already-standardized OpenAI-compatible HTTP server (`omlx serve`,
`llama-server`) and sends the exact same prompts through the exact same
measurement code to every engine, timing the full response -- not just
time-to-first-byte. The original TypeScript harness had a real bug here
once (measuring right after `fetch()` resolved, which only captures HTTP
headers arriving, produced a physically impossible 64,646 tok/s during a
live end-to-end run before it was caught and fixed); this port measures
after the full response body is read, and a regression test
(`tests/test_measure.py`) asserts that gap is never reintroduced.

## What "recommended" means (and doesn't)

The recommendation names the engine with the highest measured average
tokens/second **on this specific run, this specific hardware, this
specific model** -- not a general claim about which engine is best. A
different model, a different machine, or different thermal conditions can
change the answer.

## Security

Neither this package nor the npm package ever `eval()`s, dynamically
imports, or shells through a string -- every subprocess call
(`llama-server`, `omlx`) is a fixed argv list (`subprocess.Popen([command,
*args], ...)`), never a shell string, so a `--model` value cannot inject
additional shell commands. **Honest note**: this project does not
currently publish SLSA provenance, Sigstore signatures, or an SBOM, and
has no OpenSSF Scorecard badge set up -- none of that infrastructure
exists yet for either distribution, so it isn't claimed here. See
[SECURITY.md](https://github.com/RudrenduPaul/InferBench/blob/main/SECURITY.md)
for the vulnerability-reporting process.

## Contributing

See [CONTRIBUTING.md](https://github.com/RudrenduPaul/InferBench/blob/main/CONTRIBUTING.md).

```bash
cd python
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0, see [LICENSE](https://github.com/RudrenduPaul/InferBench/blob/main/LICENSE).
