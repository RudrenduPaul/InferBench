# Getting started

InferBench benchmarks whichever supported local-LLM-inference engines are
installed on your own machine, against a fixed, varied prompt set, and
reports the real, measured tokens/second for each. It ships as two
independent, equally first-class packages: an npm package (`inferbench-cli`,
JavaScript/TypeScript) and a PyPI package (`inferbench-cli`, Python). Pick
whichever fits your toolchain, or install both -- they measure the same way
and report the same shape of result.

**Supported engines in this v0.1 release: `omlx` and `llama.cpp`.** That is
the complete list today. Both packages start each engine's own
OpenAI-compatible HTTP server and send it the same requests -- see
[concepts.md](./concepts.md) for why the two engines needed different
model-acquisition handling.

## Install

**npm (JS/TS CLI):**

```bash
npm install -g inferbench-cli
# or run it once without installing:
npx inferbench-cli run --engines llama.cpp --model "<repo>:<quant>"
```

**pip (Python library + CLI):**

```bash
pip install inferbench-cli
```

Neither package installs an inference engine for you -- you need at least
one of these already on your machine:

- **llama.cpp**: `brew install llama.cpp` (macOS) or build from
  [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)
- **omlx**: `brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx`
  (Apple Silicon only)

## Your first run

```bash
# npm CLI
npx inferbench-cli run --engines llama.cpp --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"

# Python CLI (after `pip install inferbench-cli`)
inferbench run --engines llama.cpp --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"
```

Real output from the Python CLI, a genuine run against a live `llama-server`
process on an Apple M4 (16GB) -- the npm CLI's output is line-for-line
identical except for the `npx inferbench-cli` vs `inferbench` framing:

```
Hardware: Apple M4 (darwin/arm64), 16.0GB

llama.cpp: starting server...
llama.cpp: warming up...
llama.cpp: [1/8] benchmarking...
...
llama.cpp: [8/8] benchmarking...

Results:
  llama.cpp: avg 36.86 tok/s (range 29.77-41.21, n=8)

Recommendation: llama.cpp -- highest measured throughput on this run (36.86 tok/s avg) -- specific to this hardware and model, not a universal ranking
```

Every number above came from an actual run on real hardware during this
package's own verification -- not an illustrative placeholder. Your own
numbers will differ: they depend on your hardware, your model, and your
machine's state at the moment you run it, which is the entire reason this
tool measures live instead of quoting a fixed benchmark.

Try `omlx` the same way (model must already be present under
`~/.omlx/models/<name>` first -- see [concepts.md](./concepts.md)):

```bash
inferbench run --engines omlx --model "qwen2.5-1.5b-instruct-4bit"
```

Exit code `0` means at least one engine was tested successfully; `1` means
a usage error (an unknown `--engines` name) or no supported engine was
found installed. The Python CLI has one small, documented divergence for a
missing required flag -- see [concepts.md](./concepts.md#exit-codes).

## Using the library instead of the CLI

**Honest note on parity here**: the npm package's `package.json` points
`main` at `dist/cli.js` (the CLI script itself, which runs the command
parser as a side effect on import) and does not currently declare a
separate library entry point or an `exports` map -- its public interface
today is the CLI only, even though the underlying modules
(`src/benchmark.ts`, `src/hardware/detect.ts`, etc.) exist as regular ES
modules. The Python port adds a clean, documented library surface that the
npm package does not yet have:

**Python:**

```python
from inferbench import benchmark_engine, detect_hardware, all_engines, recommend

hardware = detect_hardware()
results = [
    benchmark_engine(adapter, model="qwen2.5-1.5b-instruct-4bit")
    for adapter in all_engines()
]
best = recommend(results)
```

## Next steps

- [concepts.md](./concepts.md) -- the measurement architecture, the
  hardware detector, the recommendation rule, and the exit-code contract.
- [integrations/ci.md](./integrations/ci.md) -- why InferBench is
  deliberately not something you run as a routine CI gate, and what the
  repo's own CI does instead (an install-smoke-test, not a full benchmark).
- The [project README](../README.md) for the full comparison and the
  original TypeScript source.
