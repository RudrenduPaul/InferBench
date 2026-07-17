# Python examples

Each numbered subdirectory is a real, runnable script against the actual
`inferbench` Python library (`from inferbench import benchmark_engine,
...`), not pseudocode. Every script talks to whichever engines are
actually installed on your machine -- none of them fabricate output when
an engine isn't present; they report `not installed` plainly instead.

Install the package first (editable install from this checkout, or `pip
install inferbench-cli` from PyPI both work identically):

```bash
cd python
pip install -e .
```

Then run any example directly (you need at least one of `omlx` or
`llama.cpp` installed, plus a model already available to it -- see the
[project README](../../README.md) for install instructions per engine):

```bash
python3 examples/01-basic-run/run.py qwen2.5-1.5b-instruct-4bit
python3 examples/02-ci-gate/gate.py qwen2.5-1.5b-instruct-4bit 20
python3 examples/03-json-report/report.py qwen2.5-1.5b-instruct-4bit report.json
```

| Example | What it demonstrates |
| --- | --- |
| [01-basic-run](./01-basic-run/) | The core library calls: `detect_hardware()`, `benchmark_engine()` per installed engine, `recommend()`, printing a human-readable summary -- the same functions `inferbench run` itself calls internally. |
| [02-ci-gate](./02-ci-gate/) | Using the library as a performance-floor gate: fail (non-zero exit) if the best measured throughput falls below a minimum tok/s, suitable for a scheduled job on fixed hardware (see [docs/integrations/ci.md](../../docs/integrations/ci.md) for why this is not recommended as a per-PR gate). |
| [03-json-report](./03-json-report/) | The agent-native use case: building a full `BenchmarkReport` in-process and serializing it to JSON with the same camelCase field names the npm CLI's `--json` output uses. |
