# InferBench

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

```bash
npm install -g inferbench-cli
# or, no install:
npx inferbench-cli run --engines llama.cpp --model "<repo>:<quant>"
```

Requires Node.js >=18. At least one supported engine must already be installed (InferBench does not install engines for you):

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

## FAQ

**Does InferBench download models for me?**
For llama.cpp, yes -- pass a Hugging Face repo spec and `llama-server`'s own `-hf` flag downloads and caches it. For omlx, no -- omlx's `serve` command only discovers models already present in a local directory, so you need to have the model downloaded there first.

**Does any data leave my machine?**
No. Every benchmark request goes to a server InferBench itself started on `127.0.0.1`. Nothing is uploaded anywhere.

**Why does `--engines` sometimes need a different `--model` value per engine?**
Because `omlx` and `llama.cpp` have genuinely different model-acquisition mechanisms -- see the Known v0.1 limitation note in Quickstart above.

**Is the recommendation a guarantee this engine is fastest for me generally?**
No. It's the fastest engine measured on this exact run. Re-run it -- your own hardware, your own model, your own moment -- rather than trusting a number from a different machine or a different day.

## Contributing

Issues and PRs welcome. Known deferred scope includes additional engine adapters, a hosted fleet dashboard, and richer recommendation scoring -- open an issue if you'd like to pick one of these up.

## License

Apache 2.0.
