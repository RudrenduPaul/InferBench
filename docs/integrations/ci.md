# CI integrations

**Honest framing up front**: InferBench is a benchmark tool for a human
to run against their own hardware, not a routine CI gate. A full run
downloads a multi-gigabyte model and spends real wall-clock time
generating tokens against it -- appropriate for a one-off decision
("which engine should I use on this machine"), not for running on every
pull request. The repo's own `.github/workflows/ci.yml` reflects this
directly: it never runs a full `inferbench run` in CI. It runs an
**install smoke test** per engine instead -- confirming the real binary
this tool targets is actually installable and responds to `--version` --
and leaves real cross-engine benchmark numbers to a human running the CLI
locally.

## What the repo's own CI does

```yaml
omlx-install-smoke-test:
  name: omlx install smoke test (macOS/Apple Silicon)
  runs-on: macos-14
  steps:
    - run: brew tap jundot/omlx https://github.com/jundot/omlx
    - run: brew trust jundot/omlx
    - run: brew install omlx
    - run: omlx --version

llamacpp-install-smoke-test:
  name: llama.cpp install smoke test (Linux)
  runs-on: ubuntu-latest
  steps:
    - run: sudo apt-get update && sudo apt-get install -y --no-install-recommends llama.cpp || echo "package unavailable via apt, falling back to build check only"
    - run: which llama-server || echo "llama-server not present via apt on this runner -- acceptable for a smoke test, not a hard CI failure"
```

Neither job downloads a model or calls `inferbench run`/`inferbench.run`.
They exist to catch "the installer for this engine is broken" before a
user hits it, not to catch a performance regression.

## If you still want InferBench in your own CI

Two reasonable, narrower uses, both opt-in and both accepting the real
cost of a model download:

**1. A scheduled (not per-PR) nightly job**, to track whether an engine
upgrade changed measured throughput on a fixed self-hosted runner with
consistent hardware:

```yaml
name: InferBench nightly (Python CLI)
on:
  schedule:
    - cron: "0 6 * * *"

jobs:
  benchmark:
    runs-on: self-hosted  # fixed hardware -- cloud runner hardware varies run to run
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install inferbench-cli
      - run: |
          inferbench run --engines llama.cpp \
            --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M" \
            --json --out report.json
      - uses: actions/upload-artifact@v4
        with:
          name: inferbench-report
          path: report.json
```

A cloud-hosted (non-self-hosted) runner's underlying hardware is not
guaranteed stable between runs, which would make day-over-day comparisons
meaningless -- pin this to a fixed self-hosted runner if the goal is
tracking a trend over time.

**2. A one-off manual dispatch**, run by a human on demand rather than
automatically, when deciding which engine to standardize on for a specific
deployment target:

```yaml
name: InferBench manual run
on:
  workflow_dispatch:
    inputs:
      model:
        required: true

jobs:
  benchmark:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install inferbench-cli
      - run: inferbench run --model "${{ inputs.model }}" --json --out report.json
      - uses: actions/upload-artifact@v4
        with:
          name: inferbench-report
          path: report.json
```

Both of the patterns above are suggestions for how you might structure
this, not something the repository itself runs -- verify the model
download time and disk footprint on your own runner before relying on
either.
