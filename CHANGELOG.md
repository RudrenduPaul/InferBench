# Changelog

All notable changes to InferBench are documented in this file. This
changelog covers both distributions -- the npm package (`inferbench-cli`,
JS/TS) and the PyPI package (`inferbench-cli`, Python) -- since they run
the same measurement architecture against the same two supported engines;
entries note which distribution they apply to.

## [Python 0.1.0] - 2026-07-17

Python port completed, tested, and built (`inferbench-cli`, `pip install
inferbench-cli` once published). Complementary to the npm package, not a
replacement for it -- both are meant to be first-class and maintained
together. See `python/README.md` for Python-specific usage.

**Publish status, stated plainly**: the first `twine upload` attempt for
this release was rejected by PyPI with `429 Too many new projects
created` -- a registry-side abuse throttle on new-project creation for
this account, not a problem with the package itself. The wheel and sdist
were built in an external venv, `twine check`-verified, installed into a
completely fresh venv, and run end to end against real `omlx` and
`llama.cpp` binaries on real hardware (see "Verified" below) before that
attempt. Separately, and for an unrelated reason, the npm package's own
publish was blocked by a transient npm-registry rate limit (`E429`) at
the time this Python port was built -- also a registry-side issue,
tracked independently of this PyPI release. **Update**: both registry-side
limits have since cleared; `pip install inferbench-cli` and
`npm install -g inferbench-cli` both work today -- see
[pypi.org/project/inferbench-cli](https://pypi.org/project/inferbench-cli/)
and [npmjs.com/package/inferbench-cli](https://www.npmjs.com/package/inferbench-cli).

### Added

- `inferbench run --model <spec>` CLI (console script `inferbench`,
  package `inferbench`) with the same flags as the npm CLI: `--engines`,
  `--max-tokens` (default 200), `--json`, `--out <file>`, `--verbose`.
- Programmatic library API: `from inferbench import benchmark_engine,
  detect_hardware, all_engines, resolve_engines, recommend,
  compare_to_cloud`. The npm package does not currently expose an
  equivalent public library entry point (its `package.json` `main` points
  at the CLI script itself) -- this is a genuine Python-side addition, not
  parity with an existing npm feature.
- Both supported engine adapters ported as genuine Python logic:
  `LlamaCppAdapter` (Hugging Face repo spec via `llama-server -hf`) and
  `OmlxAdapter` (pre-downloaded local model directory via `omlx serve
  --model-dir`).
- The shared HTTP measurement harness (`harness/measure.py`,
  `harness/spawn_server.py`), timing each completion across the full
  response body rather than just HTTP headers -- see "Notes" below.
- The hardware detector (`hardware/detect.py`), composing `sys.platform`,
  `platform.machine()`, POSIX `os.sysconf()`, and small fixed-argv
  subprocess calls to reach the same shape of `HardwareProfile` Node's
  `os` module provides directly.
- The v0.1 recommendation rule (`recommend/config.py`): highest measured
  average tok/s among installed, successfully-tested engines.
- The static cloud-cost comparison table (`cost/cloud_comparison.py`),
  ported verbatim from the TypeScript original, with its own explicit
  "not a live quote" disclosure preserved.
- Full pytest suite (41 tests) ported from the TypeScript vitest suite,
  covering the benchmark orchestrator, hardware detector, engine registry,
  both engine adapters, the HTTP measurement harness (including a
  regression test for the header-vs-body timing bug below), the
  recommendation rule, the cloud-cost comparison, and the CLI.

### Verified

- **Real end-to-end runs against both live engines on real hardware**
  (Apple M4, 16GB): `inferbench run --engines omlx --model
  qwen2.5-1.5b-instruct-4bit` and `inferbench run --engines llama.cpp
  --model "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"` both completed
  successfully against the actual `omlx` and `llama-server` binaries,
  producing genuine measured throughput (not mocked) -- see
  `docs/getting-started.md` for the real output.
- `--json --out` produces a report whose field names are camelCase and
  match the npm CLI's own JSON shape field-for-field, verified by
  inspecting a real generated report.

### Notes

- Carries forward the TypeScript harness's own documented fix for a real
  bug: measuring elapsed time right after the HTTP response object
  resolves (rather than after its body is fully read) only captures
  headers arriving, not generation finishing, and once produced a
  physically impossible 64,646 tok/s during the original tool's live
  validation. Both `harness/measure.py` and its test suite carry this fix
  and its regression test forward.
- One documented, intentional CLI divergence from the npm package: a
  missing required `--model` flag exits `2` in the Python CLI (the
  standard `argparse`/Unix convention for a parse-time error) rather than
  the npm CLI's `1` for the same case. All other documented exit codes
  (`0` success, `1` usage error / no engine found) match.
