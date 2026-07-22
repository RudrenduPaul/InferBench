# InferBench

[![PyPI version](https://img.shields.io/pypi/v/inferbench-cli.svg)](https://pypi.org/project/inferbench-cli/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)

Every "best local LLM engine" article benchmarks someone else's machine. InferBench benchmarks yours.

```bash
npx inferbench-cli run --engines llama.cpp --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"
```

---

Local-inference engines all publish their own benchmarks, on their own hardware, in their own README. None of them tell you which one is actually fastest on the machine sitting in front of you. InferBench runs a fixed, varied prompt set against whichever supported engines are installed on your own hardware and reports real, measured tokens/second -- not a number copied from someone else's blog post.

## What it does

```bash
$ inferbench run --engines llama.cpp --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"
Hardware: Apple M4 (darwin/arm64), 16GB

llama.cpp: starting server...
llama.cpp: warming up...
llama.cpp: [1/8] benchmarking...
...
llama.cpp: [8/8] benchmarking...

Results:
  llama.cpp: avg 75.54 tok/s (range 69.54-79.78, n=8)

Recommendation: llama.cpp -- highest measured throughput on this run (75.54 tok/s avg) -- specific to this hardware and model, not a universal ranking
```

Every number above is real, produced by a live run against an actual `llama-server` process on real hardware -- not an illustrative placeholder.

## Why this exists

Local inference on consumer hardware is now the default path for a growing share of developers, and every engine's own comparison against its competitors has an obvious incentive problem: no vendor is a disinterested judge of its own numbers. InferBench has no engine of its own to sell, which is the entire point.

The harder question this tool actually answers isn't "which engine is fastest in general" -- there is no such answer, because it depends on your exact hardware, your exact model, and your exact workload. It's "which engine is fastest **right now, on this machine, for this model**" -- a question only a tool that runs on your own hardware can answer honestly.

## Install

InferBench ships two independent, equally first-class packages -- pick
whichever fits your toolchain, or install both. Neither is deprecated in
favor of the other; both run the same measurement architecture against
the same two supported engines.

```bash
# npm -- JavaScript/TypeScript CLI
npm install -g inferbench-cli
# or, no install:
npx inferbench-cli run --engines llama.cpp --model "<repo>:<quant>"

# PyPI -- Python CLI + library (genuine port, not a wrapper around the Node binary)
pip install inferbench-cli
```

**Current status**: both packages are published and installable today.
`npm install -g inferbench-cli` and `pip install inferbench-cli` both
work -- see
[npmjs.com/package/inferbench-cli](https://www.npmjs.com/package/inferbench-cli)
and [pypi.org/project/inferbench-cli](https://pypi.org/project/inferbench-cli/),
or [`python/README.md`](./python/README.md) and
[docs/getting-started.md](./docs/getting-started.md) for the Python-specific
walkthrough, and [CHANGELOG.md](./CHANGELOG.md) for each distribution's
version history.

Requires Node.js >=18 for the npm package, Python >=3.9 for the PyPI
package. At least one supported engine must already be installed either
way (InferBench does not install engines for you):

- **llama.cpp**: `brew install llama.cpp` (macOS) or build from [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)
- **omlx**: `brew tap jundot/omlx https://github.com/jundot/omlx && brew install omlx` (Apple Silicon only)

## Quickstart

```bash
# llama.cpp -- pass a Hugging Face repo spec; llama.cpp downloads and
# caches it automatically, no manual step required
inferbench run --engines llama.cpp --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"

# omlx -- pass the model-directory subdirectory name under ~/.omlx/models/;
# omlx has no CLI download flow, so the model must already be present there
# (download it once via `omlx`'s own admin dashboard, or huggingface_hub's
# snapshot_download into that directory)
inferbench run --engines omlx --model "qwen2.5-1.5b-instruct-4bit"

# Both installed engines, machine-readable output, saved to a file
inferbench run --model "<spec>" --json --out report.json
```

**Known v0.1 limitation, stated plainly:** `--model` means something different per engine (a downloadable HF spec for llama.cpp, a pre-downloaded local directory name for omlx), because the two engines have genuinely different model-acquisition capabilities -- omlx's `serve` command has no flag to pull an arbitrary model from Hugging Face directly. Running both engines against the *same* model in one command therefore needs the model already available in both engines' own expected forms.

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

Exit code `0` on a successful run with at least one engine tested; `1` on a usage error or when no supported engine is installed.

## How the measurement works

InferBench does not shell out to each engine's own benchmark tool and parse its output. That approach was in the original plan and turned out not to work at all: `omlx` has no CLI benchmark command -- its "Performance Benchmark" feature is a GUI-only, one-click action in its admin dashboard, verified directly against its real README before writing a line of adapter code.

Instead, InferBench starts each engine's own already-standardized OpenAI-compatible HTTP server (`omlx serve`, `llama-server`) and sends the exact same prompts through the exact same measurement code to every engine, timing the full response (not just time-to-first-byte -- an earlier version of this code measured elapsed time right after `fetch()` resolved, which only captures HTTP headers arriving, not generation finishing, and produced a physically impossible 64,646 tok/s during a real end-to-end test run before the bug was caught and fixed). This is the only approach that is genuinely apples-to-apples across engines with fundamentally different internals, and the only one that works at all for `omlx`.

## What "recommended" means (and doesn't)

The recommendation in every report is scoped explicitly: it names the engine with the highest measured average tokens/second **on this specific run, this specific hardware, this specific model** -- not a general claim about which engine is best. A different model, a different machine, or a different day's thermal conditions can change the answer; two runs during this tool's own development produced opposite rankings between `omlx` and `llama.cpp` on the same hardware and model, which is itself the reason this tool measures live rather than quoting a fixed number.

## Comparison

| | InferBench | A static "definitive 2026 guide" comparison article |
|---|---|---|
| Measures | Your own hardware, live | The author's machine, once |
| Reproducible by you | Yes -- rerun any time | No -- you cannot rerun someone else's blog post |
| Stays current as engines update | Yes | No -- frozen at publish date |
| Vendor-neutral | Yes -- no engine of its own | Varies by author |

## Documentation

- [docs/getting-started.md](./docs/getting-started.md) -- install, first run, and using the library instead of the CLI, for both distributions.
- [docs/concepts.md](./docs/concepts.md) -- the measurement architecture, the hardware detector, the recommendation rule, and the exit-code contract.
- [docs/integrations/ci.md](./docs/integrations/ci.md) -- why InferBench is deliberately not a per-PR CI gate, and what patterns work instead.

## Demo

Install, first run, and a real omlx benchmark against a cached model:

![InferBench install and first run: pip install inferbench-cli, then a live omlx benchmark reporting real tokens/second and a recommendation](./docs/demo.gif)

Machine-readable output written to a file with `--json --out`, useful for CI or for an agent parsing the result:

![InferBench --json --out usage: a live omlx benchmark run whose full JSON report (per-prompt tokens/second, recommendation) is printed to stdout and also saved to report.json](./docs/usage.gif)

## FAQ

**What is InferBench, exactly?**
A benchmarking tool for local-LLM-inference engines already installed on your machine -- currently `omlx` and `llama.cpp`. It runs a fixed, varied prompt set against whichever of those are present, measures real tokens/second for each, and recommends whichever one was fastest on that specific run. It ships as two packages under the same name, `inferbench-cli`: one on npm (JavaScript/TypeScript) and one on PyPI (Python).

**How is InferBench different from llama.cpp's own `llama-bench`?**
`llama-bench` (bundled with llama.cpp) only benchmarks llama.cpp itself, with fine-grained tuning knobs (batch size, cache type, thread count, and more). InferBench benchmarks *across* engines -- currently `omlx` and `llama.cpp` -- using the same prompt set and the same measurement code for both, so the resulting tokens/second numbers are directly comparable to each other on your hardware, not just tunable in isolation for one engine.

**Does InferBench work on Linux and Windows, or only macOS?**
The `llama.cpp` engine works on any platform llama.cpp itself supports (Linux, macOS, Windows), since InferBench just starts `llama-server` and measures its OpenAI-compatible endpoint. The `omlx` engine is Apple Silicon-only, matching omlx's own scope -- on Linux or Windows, `--engines omlx` reports that engine as not installed and InferBench benchmarks whatever supported engine actually is present. Node.js >=18 is required for the npm package, Python >=3.9 for the PyPI package.

**Does InferBench download models for me?**
For llama.cpp, yes -- pass a Hugging Face repo spec and `llama-server`'s own `-hf` flag downloads and caches it. For omlx, no -- omlx's `serve` command only discovers models already present in a local directory, so you need to have the model downloaded there first.

**Does any data leave my machine?**
No. Every benchmark request goes to a server InferBench itself started on `127.0.0.1`. Nothing is uploaded anywhere.

**Why does `--engines` sometimes need a different `--model` value per engine?**
Because `omlx` and `llama.cpp` have genuinely different model-acquisition mechanisms -- see the Known v0.1 limitation note in Quickstart above.

**Is the recommendation a guarantee this engine is fastest for me generally?**
No. It's the fastest engine measured on this exact run. Re-run it -- your own hardware, your own model, your own moment -- rather than trusting a number from a different machine or a different day.

**Is `--out` safe to point at a path that comes from an agent or other less-trusted input?**
Yes, with one documented restriction: `--out` rejects a relative path that resolves outside the current working directory (for example `--out ../../etc/cron.d/x`), specifically so a benchmark invoked with an agent-supplied path can't be tricked into writing outside the intended directory. An absolute path is still accepted, since that's a value the caller passed directly rather than one that escaped via `..` traversal.

**What happens if no supported engine is installed, or a run fails partway through?**
If neither `omlx` nor `llama.cpp` is found, InferBench exits with code `1` and a message naming both install commands rather than returning a silent empty result. If an engine is installed but a specific run fails, that engine's line in the report reads `FAILED` with the underlying error instead of a number -- any other engine that did complete still gets a real result and remains eligible for the recommendation.

**Can I use InferBench commercially, and is it free?**
Yes. InferBench is Apache License 2.0, which permits commercial use, modification, and redistribution with no licensing fee. It has no paid API dependency -- every benchmark request goes to a server it starts locally on your own machine.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full guide, covering both the TypeScript and Python codebases. Issues and PRs welcome. Known deferred scope includes additional engine adapters, a hosted fleet dashboard, and richer recommendation scoring -- open an issue if you'd like to pick one of these up.

## Security

See [SECURITY.md](./SECURITY.md) for the vulnerability-reporting process.

## License

Apache 2.0, see [LICENSE](./LICENSE).
